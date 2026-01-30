"""
Provides mechanisms for understanding characteristics of agent populations: age distribution, interests,
skills, beliefs, goals, routines, communication styles, etc. All plotting helpers also store the underlying
data (as DataFrames) in self.plot_data for programmatic reuse.
"""

import re
import textwrap
import warnings
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:  # Normalizer lives under extraction
    from .extraction.normalizer import Normalizer  # type: ignore
except Exception:  # pragma: no cover - fallback (normalization will degrade gracefully)
    Normalizer = None  # type: ignore

try:  # Optional TinyPerson type
    from .agent import TinyPerson  # type: ignore
except Exception:  # pragma: no cover
    TinyPerson = dict  # type: ignore


class Profiler:
    """Population profiler with basic and advanced persona facet analysis."""

    def __init__(
        self,
        attributes: Optional[List[str]] = None,
        persona_label_max_chars: int = 40,
        use_pies_for_small: bool = True,
        max_categories: int = 15,
        top_n: int = 12,
        normalization_max_clusters: int = 6,
    ) -> None:
        """Initialize the Profiler.
        
        Args:
            attributes: List of agent attributes to profile (supports dot notation for nested attrs)
            persona_label_max_chars: Maximum characters for persona labels in visualizations
            use_pies_for_small: Whether to use pie charts for small categorical distributions
            max_categories: Maximum number of categories to display in charts
            top_n: Number of top items to show in rankings
            normalization_max_clusters: Maximum number of normalized categories per facet
        """
        self.attributes = attributes or [
            "age",
            "occupation.title",
            "nationality",
        ]
        self.persona_label_max_chars = persona_label_max_chars
        self.use_pies_for_small = use_pies_for_small
        self._max_categories = max_categories
        self._top_n = top_n
        self.normalization_max_clusters = normalization_max_clusters

        # Runtime containers
        self.agents: List[Any] = []
        self.attributes_distributions = {}  # type: Dict[str, pd.DataFrame]
        self.analysis_results = {}  # type: Dict[str, Any]
        self.plot_data = {}  # type: Dict[str, pd.DataFrame]
        self._custom_analyses = (
            {}
        )  # type: Dict[str, Callable[[List[Dict[str, Any]]], Any]]
        # Cache for dynamically resolved attribute paths (retained for forward compatibility)
        self._resolved_attribute_paths = {}  # type: Dict[str, str]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def profile(
        self,
        agents: List,
        plot: bool = True,
        advanced_analysis: bool = True,
    ) -> Dict[str, Any]:
        """Profile a set of agents.

        Args:
            agents: List of TinyPerson instances.
            plot: Whether to render visualizations.
            advanced_analysis: Whether to run persona & correlation analyses.
        Returns:
            Attribute distributions (basic) – advanced results available in self.analysis_results.
        """
        # Store original agent objects (TinyPerson or dicts).
        # The TinyPerson API guarantees a .get() method supporting dot notation for persona attributes.
        # Plain dict agents are also supported via dict traversal in _get_nested_attribute.
        self.agents = list(agents)

        # Basic distributions
        self.attributes_distributions = self._compute_attributes_distributions(
            self.agents
        )

        # Advanced analyses
        if advanced_analysis and self.agents:
            # Add demographics analysis
            self.analysis_results["demographics"] = self._analyze_demographics()

            if (
                Normalizer is not None
            ):  # persona composition (robust to failures internally)
                self.analysis_results["persona_composition"] = (
                    self._analyze_persona_composition()
                )
            else:
                # Still attempt persona analysis without normalization
                self.analysis_results["persona_composition"] = (
                    self._analyze_persona_composition()
                )
            self.analysis_results["correlations"] = self._analyze_correlations()
            # Hook custom analyses
            for name, func in self._custom_analyses.items():
                try:
                    self.analysis_results[name] = func(self.agents)
                except Exception as e:  # pragma: no cover
                    warnings.warn(f"Custom analysis '{name}' failed: {e}")

        if plot:
            self.render(advanced=advanced_analysis)

        return self.attributes_distributions

    # ------------------------------------------------------------------
    # Demographics analysis
    # ------------------------------------------------------------------
    def _analyze_demographics(self) -> Dict[str, Any]:
        """Analyze demographic characteristics of the agent population."""
        results: Dict[str, Any] = {}

        # Age analysis
        ages = []
        for agent in self.agents:
            age_val = self._get_nested_attribute(agent, "age")
            if age_val is not None and isinstance(age_val, (int, float)):
                ages.append(age_val)

        if ages:
            results["age_stats"] = {
                "mean": np.mean(ages),
                "median": np.median(ages),
                "std": np.std(ages),
                "min": min(ages),
                "max": max(ages),
            }

        # Occupation diversity
        occupations = []
        for agent in self.agents:
            occ_val = self._get_nested_attribute(
                agent, "occupation.title"
            ) or self._get_nested_attribute(agent, "occupation")
            if occ_val is not None:
                # If we got the full occupation object, try to extract the title
                if isinstance(occ_val, dict) and "title" in occ_val:
                    occ_val = occ_val["title"]
                occupations.append(str(occ_val))

        if occupations:
            occ_counter = Counter(occupations)
            results["occupation_diversity"] = {
                "most_common": occ_counter.most_common(10),
                "diversity_index": self._calculate_diversity_index(occ_counter),
                "total_unique": len(occ_counter),
            }

        # Geographic diversity
        nationalities = []
        for agent in self.agents:
            nat_val = self._get_nested_attribute(
                agent, "nationality"
            ) or self._get_nested_attribute(agent, "country")
            if nat_val is not None:
                nationalities.append(str(nat_val))

        if nationalities:
            nat_counter = Counter(nationalities)
            results["geographic_diversity"] = {
                "distribution": dict(nat_counter),
                "diversity_index": self._calculate_diversity_index(nat_counter),
                "total_unique": len(nat_counter),
            }

        return results

    # ------------------------------------------------------------------
    # Advanced persona composition
    # ------------------------------------------------------------------
    def _analyze_persona_composition(self) -> Dict[str, Any]:
        """Extract and aggregate persona-related facets, returning DataFrames per facet.

        Each facet DataFrame (except likes_dislikes) has columns:
          category, count, proportion, agent_count, agent_proportion, examples
        likes_dislikes has: category, likes, dislikes, net_score, total

        Normalization (clustering) uses Normalizer when available; it may return fewer
        than the requested clusters ("up to N" semantics as per primary guidelines).
        """

        results: Dict[str, Any] = {}

        # -------------------------- helpers --------------------------
        def _extract_path(agent: Dict[str, Any], path: List[str]) -> Any:
            # Simplified access: rely on TinyPerson.get (supports dot notation) when available.
            joined = ".".join(path)
            if hasattr(agent, "get") and callable(getattr(agent, "get")):
                try:
                    return agent.get(joined)
                except Exception:
                    pass
            # Fallback for plain dict agents
            cur: Any = agent
            for seg in path:
                if isinstance(cur, dict) and seg in cur:
                    cur = cur[seg]
                else:
                    return None
            return cur

        def _collect_list_per_agent(path: List[str]) -> List[List[str]]:
            data: List[List[str]] = []
            for ag in self.agents:
                val = _extract_path(ag, path)
                if isinstance(val, list):
                    data.append([str(x).strip() for x in val if x])
                else:
                    data.append([])
            return data

        def _collect_value_per_agent(path: List[str]) -> List[List[str]]:
            data: List[List[str]] = []
            for ag in self.agents:
                val = _extract_path(ag, path)
                if isinstance(val, str):
                    data.append([val.strip()])
                else:
                    data.append([])
            return data

        def _split_sentences(items: List[str]) -> List[str]:
            pieces: List[str] = []
            for t in items:
                for p in re.split(r"[.;]\s+", t):
                    p = p.strip().strip("-•* ")
                    if p:
                        pieces.append(p)
            return pieces

        def _normalize(
            name: str, raw_tokens: List[str], target_n: int
        ) -> Dict[str, List[str]]:
            uniq = [r for r in {r for r in raw_tokens if r}]
            if not uniq:
                print(f"[DEBUG normalize:{name}] No tokens provided.")
                return {}
            print(f"[DEBUG normalize:{name}] raw_tokens={len(raw_tokens)} uniq={len(uniq)} target_n={target_n}")
            if Normalizer is None:
                print(f"[DEBUG normalize:{name}] Normalizer unavailable; returning identity clusters.")
                return {u: [u] for u in uniq}
            try:
                norm = Normalizer(uniq, n=target_n, verbose=False, max_length=self.persona_label_max_chars)  # type: ignore
                mapping = norm.normalized_mapping()  # type: ignore[attr-defined]
                print(f"[DEBUG normalize:{name}] clusters={len(mapping)}")
                # Defensive guard: if an upstream change ever lets mapping exceed target_n, warn & trim locally.
                if target_n and target_n > 0 and len(mapping) > target_n:
                    warnings.warn(
                        f"Normalizer returned {len(mapping)} clusters for '{name}' exceeding cap {target_n}; trimming locally.",
                        RuntimeWarning,
                    )
                    # Keep largest clusters (by number of originals)
                    ordered = sorted(mapping.items(), key=lambda kv: len(kv[1]), reverse=True)
                    trimmed = dict(ordered[: target_n - 1]) if target_n > 1 else {}
                    if target_n > 1:
                        # Aggregate overflow originals under 'Other'
                        overflow_originals: List[str] = []
                        for _, originals in ordered[target_n - 1 :]:
                            overflow_originals.extend(originals)
                        if overflow_originals:
                            trimmed["Other"] = overflow_originals
                    else:
                        # Single bucket scenario: collapse everything
                        overflow_all: List[str] = []
                        for _, originals in ordered:
                            overflow_all.extend(originals)
                        trimmed = {"Other": overflow_all}
                    mapping = trimmed
                    print(f"[DEBUG normalize:{name}] post-trim clusters={len(mapping)}")
                return mapping
            except Exception as e:  # pragma: no cover
                warnings.warn(
                    f"Normalization failed for {name}: {e}; using raw tokens.",
                    RuntimeWarning,
                )
                print(f"[DEBUG normalize:{name}] Exception -> fallback identity mapping.")
                return {u: [u] for u in uniq}

        def _distribution_df(
            mapping: Dict[str, List[str]],
            per_agent_tokens: List[List[str]],
            rev_lookup: Dict[str, str],
            target_n: int,  # NEW: enforce maximum categories displayed
        ) -> pd.DataFrame:
            """
            Build facet distribution with robust matching.

            Fix: Previous version produced all-zero counts because many raw tokens
            failed exact lookup in rev_lookup (normalization / whitespace / case).
            Now we:
              1. Build auxiliary lowercase lookup.
              2. Attempt direct, stripped, and lowercase matches.
              3. Track both occurrence frequency and agent coverage.
              4. Fallback to raw token frequency if every cluster count is zero.
            """
            print(f"[DEBUG distribution] agents={len(per_agent_tokens)} mapping_clusters={len(mapping)} rev_lookup_size={len(rev_lookup)}")
            total_raw = sum(len(toks) for toks in per_agent_tokens)
            print(f"[DEBUG distribution] total_raw_tokens={total_raw}")

            if not per_agent_tokens:
                print("[DEBUG distribution] Empty per_agent_tokens list.")
                return pd.DataFrame(
                    columns=[
                        "category","count","proportion","agent_count","agent_proportion","examples"
                    ]
                )

            # Raw fallback path (no normalization)
            if not mapping or not rev_lookup:
                if not mapping:
                    print("[DEBUG distribution] No mapping available -> raw frequency fallback.")
                flat = [t for ts in per_agent_tokens for t in ts if t]
                if not flat:
                    print("[DEBUG distribution] No flat tokens after flattening.")
                    return pd.DataFrame(
                        columns=[
                            "category","count","proportion","agent_count","agent_proportion","examples"
                        ]
                    )
                occ_counter = Counter(flat)
                agent_counter: Dict[str, int] = defaultdict(int)
                for ts in per_agent_tokens:
                    for tok in set(ts):
                        agent_counter[tok] += 1
                total_occ = sum(occ_counter.values())
                n_agents = len(per_agent_tokens) or 1
                rows = []
                for cat, occ in occ_counter.most_common():
                    rows.append(
                        {
                            "category": cat,
                            "count": occ,
                            "proportion": occ / total_occ,
                            "agent_count": agent_counter[cat],
                            "agent_proportion": agent_counter[cat] / n_agents,
                            "examples": [cat],
                        }
                    )
                df = pd.DataFrame(rows)
                print(f"[DEBUG distribution] Raw fallback rows={len(df)} top_sample={df.head(3).to_dict('records') if not df.empty else []}")
                # HARD CAP enforcement even in raw fallback
                if target_n and target_n > 0 and len(df) > target_n:
                    warnings.warn(
                        f"Raw fallback produced {len(df)} categories; trimming to {target_n} (including possible 'Other').",
                        RuntimeWarning,
                    )
                    kept_slots = target_n - 1 if target_n > 1 else 1
                    kept = df.head(kept_slots).copy()
                    tail = df.iloc[kept_slots:]
                    other_count = tail['count'].sum()
                    other_agent_count = tail['agent_count'].sum()
                    if target_n > 1 and (other_count > 0 or other_agent_count > 0):
                        other_row = {
                            'category': 'Other',
                            'count': other_count,
                            'proportion': 0.0,
                            'agent_count': other_agent_count,
                            'agent_proportion': 0.0,
                            'examples': tail.head(3)['category'].tolist(),
                        }
                        kept = pd.concat([kept, pd.DataFrame([other_row])], ignore_index=True)
                    total_occ2 = kept['count'].sum() or 1
                    total_agents_any2 = max(1, len(per_agent_tokens))
                    kept['proportion'] = kept['count'] / total_occ2
                    kept['agent_proportion'] = kept['agent_count'] / total_agents_any2
                    df = kept
                return df

            rev_lc: Dict[str, str] = {orig.lower(): cat for orig, cat in rev_lookup.items()}

            occurrence_counts: Dict[str, int] = defaultdict(int)
            agent_counts: Dict[str, int] = defaultdict(int)
            unmatched_tokens: List[str] = []

            def resolve(token: str) -> Optional[str]:
                if not token:
                    return None
                if token in rev_lookup:
                    return rev_lookup[token]
                t_stripped = token.strip()
                if t_stripped in rev_lookup:
                    return rev_lookup[t_stripped]
                lc = token.lower()
                if lc in rev_lc:
                    return rev_lc[lc]
                lc_stripped = t_stripped.lower()
                if lc_stripped in rev_lc:
                    return rev_lc[lc_stripped]
                return None

            for agent_idx, agent_tokens in enumerate(per_agent_tokens):
                seen_in_agent = set()
                for tok in agent_tokens:
                    cat = resolve(tok)
                    if cat:
                        occurrence_counts[cat] += 1
                        seen_in_agent.add(cat)
                    else:
                        unmatched_tokens.append(tok)
                for cat in seen_in_agent:
                    agent_counts[cat] += 1

            if unmatched_tokens:
                sample_unmatched = unmatched_tokens[:10]
                print(f"[DEBUG distribution] unmatched_tokens={len(unmatched_tokens)} sample={sample_unmatched}")

            if not occurrence_counts or all(v == 0 for v in occurrence_counts.values()):
                print("[DEBUG distribution] All cluster counts zero -> fallback to raw token counting.")
                flat = [t for ts in per_agent_tokens for t in ts if t]
                if not flat:
                    print("[DEBUG distribution] Fallback also empty.")
                    return pd.DataFrame(
                        columns=[
                            "category","count","proportion","agent_count","agent_proportion","examples"
                        ]
                    )
                occ_counter = Counter(flat)
                agent_counter: Dict[str, int] = defaultdict(int)
                for ts in per_agent_tokens:
                    for tok in set(ts):
                        agent_counter[tok] += 1
                total_occ = sum(occ_counter.values())
                n_agents = len(per_agent_tokens) or 1
                rows = []
                for cat, occ in occ_counter.most_common():
                    rows.append(
                        {
                            "category": cat,
                            "count": occ,
                            "proportion": occ / total_occ,
                            "agent_count": agent_counter[cat],
                            "agent_proportion": agent_counter[cat] / n_agents,
                            "examples": [cat],
                        }
                    )
                df = pd.DataFrame(rows)
                print(f"[DEBUG distribution] Fallback rows={len(df)} top_sample={df.head(3).to_dict('records') if not df.empty else []}")
                return df

            total_occurrences = sum(occurrence_counts.values()) or 1
            n_agents = len(per_agent_tokens) or 1
            rows: List[Dict[str, Any]] = []
            for cat, originals in mapping.items():
                occ_ct = occurrence_counts.get(cat, 0)
                a_ct = agent_counts.get(cat, 0)
                rows.append(
                    {
                        "category": cat,
                        "count": occ_ct,
                        "proportion": occ_ct / total_occurrences,
                        "agent_count": a_ct,
                        "agent_proportion": a_ct / n_agents,
                        "examples": originals[:3],
                    }
                )
            df_local = pd.DataFrame(rows).sort_values(
                ["count", "agent_count"], ascending=False
            ).reset_index(drop=True)
            print(f"[DEBUG distribution] Final rows={len(df_local)} nonzero={int((df_local['count']>0).sum())} top_sample={df_local.head(3).to_dict('records') if not df_local.empty else []}")

            # --- BEGIN patched tail of _distribution_df (after df_local is built) ---
            print(f"[DEBUG distribution] Pre-trim categories={len(df_local)} target_n={target_n}")
            if target_n and target_n > 0 and len(df_local) > target_n:
                # We reserve at most (target_n - 1) for top clusters if we will add 'Other'
                kept_slots = target_n - 1 if target_n > 1 else 1
                kept = df_local.head(kept_slots).copy()
                tail = df_local.iloc[kept_slots:]
                other_count = tail["count"].sum()
                other_agent_count = tail["agent_count"].sum()
                warnings.warn(
                    f"Trimming facet categories from {len(df_local)} to <= {target_n} (aggregating tail into 'Other' if applicable).",
                    RuntimeWarning,
                )
                if target_n > 1 and (other_count > 0 or other_agent_count > 0):
                    other_row = {
                        "category": "Other",
                        "count": other_count,
                        "proportion": 0.0,  # will recalc
                        "agent_count": other_agent_count,
                        "agent_proportion": 0.0,  # will recalc
                        "examples": [r["category"] for r in tail.head(3).to_dict("records")],
                    }
                    kept = pd.concat([kept, pd.DataFrame([other_row])], ignore_index=True)
                    # Recompute proportions on trimmed set
                    total_occ = kept["count"].sum() or 1
                    total_agents_any = max(1, len(per_agent_tokens))
                    kept["proportion"] = kept["count"] / total_occ
                    kept["agent_proportion"] = kept["agent_count"] / total_agents_any
                    df_local = kept
                    print(f"[DEBUG distribution] Trimmed to {len(df_local)} (with 'Other'), target_n={target_n}.")
                else:
                    df_local = kept
                    total_occ = df_local["count"].sum() or 1
                    total_agents_any = max(1, len(per_agent_tokens))
                    df_local["proportion"] = df_local["count"] / total_occ
                    df_local["agent_proportion"] = df_local["agent_count"] / total_agents_any
                    print(f"[DEBUG distribution] Trimmed to {len(df_local)} (no 'Other'), target_n={target_n}.")
            else:
                # Recompute proportions to ensure consistency (esp. if earlier fallback path)
                total_occ = df_local["count"].sum() or 1
                total_agents_any = max(1, len(per_agent_tokens))
                if "proportion" in df_local.columns:
                    df_local["proportion"] = df_local["count"] / total_occ
                if "agent_proportion" in df_local.columns:
                    df_local["agent_proportion"] = df_local["agent_count"] / total_agents_any
            print(f"[DEBUG distribution] Final (post-trim) categories={len(df_local)}")
            return df_local.reset_index(drop=True)
            # --- END patched tail ---

        # -------------------------- facets (debug instrumentation) --------------------------
        # 1. Interests
        interests_per_agent = _collect_list_per_agent(["interests"])
        interests_tokens = [i for sub in interests_per_agent for i in sub]
        print(f"[DEBUG facet:interests] agents={len(interests_per_agent)} raw_tokens={len(interests_tokens)} sample={interests_tokens[:5]}")
        interests_map = _normalize("interests", interests_tokens, target_n=self.normalization_max_clusters)
        rev_interests = {o: c for c, lst in interests_map.items() for o in lst}
        results["interests"] = _distribution_df(
            interests_map, interests_per_agent, rev_interests, self.normalization_max_clusters
        )
        if isinstance(results.get('interests'), pd.DataFrame):
            print('[DEBUG facet:interests] categories=', results['interests']['category'].tolist())

        # 2. Skills (keep existing debug + add summary after distribution)
        skills_per_agent = _collect_list_per_agent(["skills"])
        skills_tokens = [s for sub in skills_per_agent for s in sub]
        print(f"DEBUG Skills: skills_per_agent sample: {skills_per_agent[:2]}")
        print(f"DEBUG Skills: skills_tokens sample: {skills_tokens[:10]}")
        skills_map = _normalize("skills", skills_tokens, target_n=self.normalization_max_clusters)
        print(f"DEBUG Skills: skills_map: {skills_map}")
        rev_skills = {o: c for c, lst in skills_map.items() for o in lst}
        print(f"DEBUG Skills: rev_skills sample: {dict(list(rev_skills.items())[:5])}")
        results["skills"] = _distribution_df(
            skills_map, skills_per_agent, rev_skills, self.normalization_max_clusters
        )
        if isinstance(results["skills"], pd.DataFrame):
            print(f"[DEBUG facet:skills] rows={len(results['skills'])} nonzero={(results['skills']['count']>0).sum() if not results['skills'].empty else 0}")
            print('[DEBUG facet:skills] categories=', results['skills']['category'].tolist())

        # 3. Beliefs / Values
        beliefs_per_agent = _collect_list_per_agent(["beliefs"])
        beliefs_tokens = _split_sentences([b for sub in beliefs_per_agent for b in sub])
        print(f"[DEBUG facet:beliefs] raw_sentences={len(beliefs_tokens)} sample={beliefs_tokens[:5]}")
        beliefs_map = _normalize("beliefs", beliefs_tokens, target_n=self.normalization_max_clusters)
        rev_beliefs = {o: c for c, lst in beliefs_map.items() for o in lst}
        per_agent_belief_tokens = [_split_sentences(sub) for sub in beliefs_per_agent]
        results["beliefs"] = _distribution_df(
            beliefs_map, per_agent_belief_tokens, rev_beliefs, self.normalization_max_clusters
        )
        if isinstance(results["beliefs"], pd.DataFrame):
            print(f"[DEBUG facet:beliefs] rows={len(results['beliefs'])} nonzero={(results['beliefs']['count']>0).sum() if not results['beliefs'].empty else 0}")
            print('[DEBUG facet:beliefs] categories=', results['beliefs']['category'].tolist())

        # 4. Goals
        goals_per_agent = _collect_list_per_agent(["goals"])
        goal_tokens = _split_sentences([g for sub in goals_per_agent for g in sub])
        print(f"[DEBUG facet:goals] raw_sentences={len(goal_tokens)} sample={goal_tokens[:5]}")
        goals_map = _normalize("goals", goal_tokens, target_n=self.normalization_max_clusters)
        rev_goals = {o: c for c, lst in goals_map.items() for o in lst}
        per_agent_goal_tokens = [_split_sentences(sub) for sub in goals_per_agent]
        results["goals"] = _distribution_df(goals_map, per_agent_goal_tokens, rev_goals, self.normalization_max_clusters)
        if isinstance(results["goals"], pd.DataFrame):
            print(f"[DEBUG facet:goals] rows={len(results['goals'])} nonzero={(results['goals']['count']>0).sum() if not results['goals'].empty else 0}")
            print('[DEBUG facet:goals] categories=', results['goals']['category'].tolist())

        # 5. Likes / Dislikes sentiment (updated counting to real frequencies + debug)
        likes_per_agent = _collect_list_per_agent(["likes"])
        dislikes_per_agent = _collect_list_per_agent(["dislikes"])
        likes_tokens = [l for sub in likes_per_agent for l in sub]
        dislikes_tokens = [d for sub in dislikes_per_agent for d in sub]
        likes_map = _normalize("likes", likes_tokens, target_n=self.normalization_max_clusters)
        dislikes_map = _normalize("dislikes", dislikes_tokens, target_n=self.normalization_max_clusters)
        rev_likes = {o: c for c, lst in likes_map.items() for o in lst}
        rev_dislikes = {o: c for c, lst in dislikes_map.items() for o in lst}
        like_counts = Counter(
            rev_likes.get(t, t) for t in likes_tokens if t
        )  # fallback to token if missing
        dislike_counts = Counter(
            rev_dislikes.get(t, t) for t in dislikes_tokens if t
        )
        sentiment_categories = set(like_counts.keys()) | set(dislike_counts.keys())
        rows_ld: List[Dict[str, Any]] = []
        for cat in sentiment_categories:
            l_ct = like_counts.get(cat, 0)
            d_ct = dislike_counts.get(cat, 0)
            if l_ct == 0 and d_ct == 0:
                continue
            rows_ld.append(
                {
                    "category": cat,
                    "likes": l_ct,
                    "dislikes": d_ct,
                    "net_score": l_ct - d_ct,
                    "total": l_ct + d_ct,
                }
            )
        results["likes_dislikes"] = (
            pd.DataFrame(rows_ld)
            .sort_values("net_score", ascending=False)
            .reset_index(drop=True)
            if rows_ld
            else pd.DataFrame(
                columns=["category", "likes", "dislikes", "net_score", "total"]
            )
        )
        if isinstance(results["likes_dislikes"], pd.DataFrame):
            print(f"[DEBUG facet:likes_dislikes] rows={len(results['likes_dislikes'])} sample={results['likes_dislikes'].head(3).to_dict('records')}")
            # --- NEW: enforce cap consistent with normalization_max_clusters ---
            ld_df = results["likes_dislikes"]
            cap = self.normalization_max_clusters
            if cap and cap > 0 and len(ld_df) > cap:
                # Keep top 'cap' by total (likes+dislikes); aggregate tail
                ld_df = ld_df.sort_values("total", ascending=False).reset_index(drop=True)
                head_df = ld_df.head(cap).copy()
                tail = ld_df.iloc[cap:]
                other_likes = tail["likes"].sum()
                other_dislikes = tail["dislikes"].sum()
                if other_likes + other_dislikes > 0:
                    other_row = pd.DataFrame([{
                        "category": "Other",
                        "likes": other_likes,
                        "dislikes": other_dislikes,
                        "net_score": other_likes - other_dislikes,
                        "total": other_likes + other_dislikes,
                    }])
                    head_df = pd.concat([head_df, other_row], ignore_index=True)
                results["likes_dislikes"] = head_df
                print(f"[DEBUG facet:likes_dislikes] trimmed to {len(head_df)} categories (cap={cap})")
            print('[DEBUG facet:likes_dislikes] categories=', results['likes_dislikes']['category'].tolist())
        # 6. Routines
        routine_paths = [
            ["behaviors", "routines", "morning"],
            ["behaviors", "routines", "workday"],
            ["behaviors", "routines", "evening"],
            ["behaviors", "routines", "weekend"],
        ]
        routines_per_agent: List[List[str]] = [[] for _ in self.agents]
        for path in routine_paths:
            current = _collect_list_per_agent(path)
            for i, lst in enumerate(current):
                routines_per_agent[i].extend(lst)
        routines_tokens = _split_sentences(
            [r for sub in routines_per_agent for r in sub]
        )
        routines_map = _normalize("routines", routines_tokens, target_n=self.normalization_max_clusters)
        rev_routines = {o: c for c, lst in routines_map.items() for o in lst}
        per_agent_routine_tokens = [_split_sentences(sub) for sub in routines_per_agent]
        results["routines"] = _distribution_df(
            routines_map, per_agent_routine_tokens, rev_routines, self.normalization_max_clusters
        )
        if isinstance(results["routines"], pd.DataFrame):
            print(f"[DEBUG facet:routines] rows={len(results['routines'])} nonzero={(results['routines']['count']>0).sum() if not results['routines'].empty else 0}")
            print('[DEBUG facet:routines] categories=', results['routines']['category'].tolist())

        # 7. Relationship roles
        roles_per_agent: List[List[str]] = []
        role_pattern = re.compile(
            r"boss|manager|colleague|friend|partner|spouse|mentor|peer|client"
        )
        for ag in self.agents:
            found: List[str] = []
            rels = ag.get("relationships", []) if isinstance(ag, dict) else []
            if isinstance(rels, list):
                for r in rels:
                    if isinstance(r, dict):
                        desc = str(r.get("description", ""))
                        matches = role_pattern.findall(desc.lower())
                        if matches:
                            found.extend(matches)
            roles_per_agent.append(found)
        roles_tokens = [r for sub in roles_per_agent for r in sub]
        roles_map = _normalize("roles", roles_tokens, target_n=self.normalization_max_clusters)
        rev_roles = {o: c for c, lst in roles_map.items() for o in lst}
        results["relationship_roles"] = _distribution_df(
            roles_map, roles_per_agent, rev_roles, self.normalization_max_clusters
        )
        if isinstance(results["relationship_roles"], pd.DataFrame):
            print(f"[DEBUG facet:relationship_roles] rows={len(results['relationship_roles'])} nonzero={(results['relationship_roles']['count']>0).sum() if not results['relationship_roles'].empty else 0}")
            print('[DEBUG facet:relationship_roles] categories=', results['relationship_roles']['category'].tolist())

        # 8. Communication style
        style_value_per_agent = _collect_value_per_agent(["style"])
        traits_list_per_agent = _collect_list_per_agent(["personality", "traits"])
        style_tokens_per_agent: List[List[str]] = []
        style_tokens: List[str] = []
        for i in range(len(style_value_per_agent)):
            combined: List[str] = []
            combined.extend(style_value_per_agent[i])
            combined.extend(traits_list_per_agent[i])
            split_tokens: List[str] = []
            for raw in combined:
                # Don't split at all - preserve full semantic descriptions including multi-sentence text
                t = raw.strip()
                if t:
                    split_tokens.append(t)
                    style_tokens.append(t)
            style_tokens_per_agent.append(split_tokens)
        styles_map = _normalize("communication_style", style_tokens, target_n=self.normalization_max_clusters)
        rev_styles = {o: c for c, lst in styles_map.items() for o in lst}
        results["communication_style"] = _distribution_df(
            styles_map, style_tokens_per_agent, rev_styles, self.normalization_max_clusters
        )
        if isinstance(results["communication_style"], pd.DataFrame):
            print(f"[DEBUG facet:communication_style] rows={len(results['communication_style'])} nonzero={(results['communication_style']['count']>0).sum() if not results['communication_style'].empty else 0}")
            # HIGH DETAIL DEBUG for communication style
            print('[DEBUG facet:communication_style] style_tokens=', style_tokens)
            print('[DEBUG facet:communication_style] mapping=', styles_map)
            print('[DEBUG facet:communication_style] rev_styles(sample)=', list(rev_styles.items())[:15])
            print('[DEBUG facet:communication_style] per_agent_tokens(sample)=', style_tokens_per_agent[:3])
            print('[DEBUG facet:communication_style] full_df=', results['communication_style'].to_dict('records'))
            print('[DEBUG facet:communication_style] categories=', results['communication_style']['category'].tolist())

        # 9. Health
        health_value_per_agent = _collect_value_per_agent(["health"])
        health_tokens_per_agent: List[List[str]] = []
        health_tokens: List[str] = []
        for vals in health_value_per_agent:
            tokens: List[str] = []
            for h in vals:
                # Don't split at all - preserve full semantic descriptions including multi-sentence text
                t = h.strip()
                if t:
                    tokens.append(t)
                    health_tokens.append(t)
            health_tokens_per_agent.append(tokens)
        health_map = _normalize("health", health_tokens, target_n=self.normalization_max_clusters)
        rev_health = {o: c for c, lst in health_map.items() for o in lst}
        results["health"] = _distribution_df(
            health_map, health_tokens_per_agent, rev_health, self.normalization_max_clusters
        )
        if isinstance(results["health"], pd.DataFrame):
            print(f"[DEBUG facet:health] rows={len(results['health'])} nonzero={(results['health']['count']>0).sum() if not results['health'].empty else 0}")
            print('[DEBUG facet:health] categories=', results['health']['category'].tolist())

        # 10. Personality traits
        personality_per_agent = _collect_list_per_agent(["personality", "traits"])
        personality_tokens = [
            re.sub(r"^you are ", "", t.strip(), flags=re.I)
            for sub in personality_per_agent
            for t in sub
        ]
        traits_map = _normalize("personality_traits", personality_tokens, target_n=self.normalization_max_clusters)
        rev_traits = {o: c for c, lst in traits_map.items() for o in lst}
        per_agent_trait_tokens = [
            [re.sub(r"^you are ", "", t.strip(), flags=re.I) for t in sub]
            for sub in personality_per_agent
        ]
        results["personality_traits"] = _distribution_df(
            traits_map, per_agent_trait_tokens, rev_traits, self.normalization_max_clusters
        )
        if isinstance(results["personality_traits"], pd.DataFrame):
            print(f"[DEBUG facet:personality_traits] rows={len(results['personality_traits'])} nonzero={(results['personality_traits']['count']>0).sum() if not results['personality_traits'].empty else 0}")
            print('[DEBUG facet:personality_traits] categories=', results['personality_traits']['category'].tolist())

        # Final summary
        print("[DEBUG persona_composition] facets_completed=" + ", ".join(results.keys()))
        # Global safety check: ensure each facet respects normalization_max_clusters (+1 for 'Other').
        cap = self.normalization_max_clusters
        if cap and cap > 0:
            for facet, df in results.items():
                if isinstance(df, pd.DataFrame) and not df.empty and "category" in df.columns:
                    unique_cats = df["category"].nunique()
                    if unique_cats > cap + 1:  # allow 'Other'
                        warnings.warn(
                            f"Facet '{facet}' has {unique_cats} categories exceeding cap {cap} (incl. 'Other'). Consider investigation.",
                            RuntimeWarning,
                        )
                        print(f"[DEBUG persona_composition] WARNING facet '{facet}' categories={unique_cats} > cap+1={cap+1}")
        return results

    def _plot_persona_composition(
        self,
        show_empty: bool = False,
        include_extra_facets: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Plot persona composition facets.
        Args:
            show_empty: if True, render placeholder charts for empty facets (helps layout visibility).
            include_extra_facets: if True, include routines, relationship roles, health, personality traits.
        """
        comp = self.analysis_results.get("persona_composition", {})
        if not isinstance(comp, dict) or not comp:
            print("Warning: No persona composition data found")
            return {}

        print(f"Persona composition keys found: {list(comp.keys())}")

        # Base panels (original)
        base_panels = [
            ("interests", "Interests"),
            ("skills", "Skills"),
            ("beliefs", "Beliefs / Values"),
            ("goals", "Goals"),
            ("likes_dislikes", "Likes vs Dislikes"),
            ("communication_style", "Communication Style"),
        ]
        if include_extra_facets:
            # Add remaining facets collected in analysis
            base_panels.extend(
                [
                    ("routines", "Routines"),
                    ("relationship_roles", "Relationship Roles"),
                    ("health", "Health"),
                    ("personality_traits", "Personality Traits"),
                ]
            )

        selected = [p for p in base_panels if p[0] in comp]
        if not selected:
            print("Warning: No valid panels found among selected facets.")
            return {}

        n = len(selected)
        n_cols = 2 if n > 1 else 1
        n_rows = (n + n_cols - 1) // n_cols

        def _short(text: str) -> str:
            if len(text) <= self.persona_label_max_chars:
                return text
            first = re.split(r"[.;]\s", text)[0]
            if len(first) <= self.persona_label_max_chars:
                return first
            return textwrap.shorten(text, width=self.persona_label_max_chars, placeholder="…")

        max_label = 0
        for key, _ in selected:
            df = comp[key]
            if isinstance(df, pd.DataFrame) and not df.empty and "category" in df.columns:
                for cat in df.head(10)["category"].tolist():
                    max_label = max(max_label, len(_short(cat)))

        # Improved sizing for pie charts - make them more compact and properly fit 2 per row
        col_width = 5.5  # Reduced from 7.2 to fit better side by side
        row_height = 4.2  # Fixed height for pie charts, regardless of label length
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(col_width * n_cols, row_height * n_rows))
        axes = np.array(axes).reshape(-1)

        plots_created = 0
        for i, (key, title) in enumerate(selected):
            ax = axes[i]
            df = comp.get(key, pd.DataFrame())
            empty_df = (
                not isinstance(df, pd.DataFrame)
                or df.empty
                or "category" not in df.columns
            )
            if empty_df:
                print(f"[DEBUG persona_plot] facet '{key}' empty -> {'showing placeholder' if show_empty else 'hidden'}")
                if show_empty:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=9)
                    ax.set_title(f"{title} (empty)")
                    plots_created += 1
                else:
                    ax.set_visible(False)
                continue

            # Likes / dislikes specialized chart
            if key == "likes_dislikes":
                top_df = df.head(15)
                if "net_score" in top_df.columns:
                    top_df = top_df.sort_values("net_score", ascending=True)
                if top_df.empty and show_empty:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=9)
                    ax.set_title(f"{title} (empty)")
                    plots_created += 1
                    continue
                if top_df.empty:
                    ax.set_visible(False)
                    continue
                ax.barh(
                    top_df["category"],
                    top_df.get("net_score", pd.Series([0] * len(top_df))),
                    color=[
                        "#d62728" if v < 0 else "#2ca02c"
                        for v in top_df.get("net_score", pd.Series([0] * len(top_df)))
                    ],
                )
                ax.axvline(0, color="black", linewidth=0.7)
                ax.set_title(title)
                ax.tick_params(labelsize=7)
                plots_created += 1
                continue

            plot_df = df.copy().head(18)

            # Select metric
            if "count" in plot_df.columns and plot_df["count"].sum() > 0:
                metric = "count"
            elif "proportion" in plot_df.columns and plot_df["proportion"].sum() > 0:
                metric = "proportion"
            elif "agent_proportion" in plot_df.columns and plot_df["agent_proportion"].sum() > 0:
                metric = "agent_proportion"
            else:
                # All zero metrics
                if show_empty:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=9)
                    ax.set_title(f"{title} (empty)")
                    plots_created += 1
                else:
                    ax.set_visible(False)
                print(f"[DEBUG persona_plot] facet '{key}' all-zero metrics -> {'placeholder' if show_empty else 'hidden'}")
                continue

            if metric in plot_df.columns:
                nz = plot_df[plot_df[metric] > 0]
                if not nz.empty:
                    plot_df = nz

            if plot_df.empty:
                if show_empty:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=9)
                    ax.set_title(f"{title} (empty)")
                    plots_created += 1
                else:
                    ax.set_visible(False)
                print(f"[DEBUG persona_plot] facet '{key}' empty after filtering -> {'placeholder' if show_empty else 'hidden'}")
                continue

            plots_created += 1
            plot_df["short_category"] = plot_df["category"].apply(_short)
            vals_raw = plot_df.get(metric, pd.Series([1] * len(plot_df)))
            try:
                vals = pd.to_numeric(vals_raw, errors="coerce").fillna(0)
            except Exception:
                vals = pd.Series([1] * len(plot_df))
            if (vals <= 0).all():
                if show_empty:
                    ax.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=9)
                    ax.set_title(f"{title} (empty)")
                else:
                    ax.set_visible(False)
                print(f"[DEBUG persona_plot] facet '{key}' non-positive values -> {'placeholder' if show_empty else 'hidden'}")
                continue

            # Create pie chart with improved proportions and always show percentages
            def make_autopct(total_sum):
                def autopct_func(pct):
                    return f'{pct:.1f}%' if pct >= 3 else ''  # Only show if >= 3% to avoid clutter
                return autopct_func
            
            ax.pie(
                vals,
                labels=[textwrap.fill(c, 25) for c in plot_df["short_category"]],  # Reduced wrap width for better fit
                autopct=make_autopct(vals.sum()) if vals.sum() > 0 else None,
                startangle=140,
                textprops={"fontsize": 8},  # Slightly larger font for better readability
                wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
                pctdistance=0.85,  # Position percentage labels closer to edge
            )
            ax.axis("equal")
            ax.set_title(title, fontsize=10)

        # Hide extra axes
        for j in range(len(selected), len(axes)):
            axes[j].set_visible(False)

        if plots_created == 0:
            plt.close(fig)
            print("Warning: No persona composition data to plot - all charts are empty")
            return {}

        plt.tight_layout()
        plt.show()
        self.plot_data.update({f"persona_{k}": v for k, v in comp.items()})
        return comp

    def render(self, advanced: bool = True) -> None:
        """
        Renders comprehensive visualizations of the agent population analysis.
        """
        # Basic attribute distributions
        self._plot_basic_distributions()

        if advanced and self.analysis_results:
            self._plot_advanced_analysis()

    def _plot_basic_distributions(self) -> Dict[str, pd.DataFrame]:
        """Plot basic attribute distributions with improved styling.

        Returns:
            Dict[str, DataFrame]: mapping attribute -> DataFrame (columns: value,count)
        """
        results: Dict[str, pd.DataFrame] = {}
        if not self.attributes:
            return results

        # One subplot page can hold at most 6 charts comfortably. Chunk all attributes; we'll skip empty ones individually.
        def chunks(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        any_plotted = False
        for page_attrs in chunks(self.attributes, 6):
            n_attrs = len(page_attrs)
            n_cols = min(3, n_attrs)
            n_rows = (n_attrs + n_cols - 1) // n_cols
            fig, axes = plt.subplots(
                n_rows, n_cols, figsize=(5.2 * n_cols, 3.8 * n_rows)
            )
            if n_attrs == 1:
                axes = [axes]
            else:
                axes = axes.flatten()

            for i, attribute in enumerate(page_attrs):
                ax = axes[i]
                if attribute not in self.attributes_distributions:
                    ax.set_visible(False)
                    continue
                dist_obj = self.attributes_distributions[attribute]
                # Allow Series or DataFrame; treat empty / length 0 as skip
                try:
                    if dist_obj is None or (hasattr(dist_obj, "empty") and dist_obj.empty) or len(dist_obj) == 0:  # type: ignore[arg-type]
                        ax.set_visible(False)
                        continue
                except Exception:
                    ax.set_visible(False)
                    continue
                any_plotted = True
                series = self.attributes_distributions[attribute]
                if isinstance(series, pd.DataFrame):  # safeguard
                    values_series = series.iloc[:, 0]
                else:
                    values_series = series
                # Prepare categorical series (Series index=category, value=count)
                cat_series = values_series.sort_values(ascending=False)
                if len(cat_series) > self._max_categories:
                    top = cat_series.head(self._max_categories - 1)
                    other_sum = cat_series.iloc[self._max_categories - 1 :].sum()
                    if other_sum > 0:
                        cat_series = pd.concat([top, pd.Series({"Other": other_sum})])
                    else:
                        cat_series = top
                # Build DataFrame and store
                df_plot = cat_series.reset_index()
                df_plot.columns = ["value", "count"]
                results[attribute] = df_plot
                self.plot_data[f"basic_{attribute}"] = df_plot
                # Decide plot type (pie vs bar) and orientation for readability
                if (
                    self.use_pies_for_small
                    and 2 <= len(df_plot) <= 12
                    and df_plot["count"].sum() > 0
                ):
                    # Pie chart for compact categorical distributions
                    ax.pie(
                        df_plot["count"],
                        labels=[textwrap.fill(str(v), 25) for v in df_plot["value"]],
                        autopct="%1.0f%%",
                        startangle=140,
                        textprops={"fontsize": 7},
                    )
                    ax.axis("equal")
                    ax.set_title(attribute.replace("_", " ").title())
                else:
                    horizontal = (
                        len(df_plot) > 8
                        or max(len(str(v)) for v in df_plot["value"]) > 18
                    )
                    palette = sns.color_palette("husl", len(df_plot))
                    if horizontal:
                        sns.barplot(
                            data=df_plot,
                            y="value",
                            x="count",
                            ax=ax,
                            palette=palette,
                        )
                        ax.set_ylabel("")
                    else:
                        sns.barplot(
                            data=df_plot,
                            x="value",
                            y="count",
                            ax=ax,
                            palette=palette,
                        )
                        ax.set_xlabel("")
                        ax.tick_params(axis="x", rotation=35)
                    title = (
                        f"{attribute.replace('_',' ').title()}"
                        if not horizontal
                        else textwrap.fill(attribute.replace("_", " ").title(), 25)
                    )
                    ax.set_title(title)
                    for c in ax.containers:
                        ax.bar_label(c, fontsize=8, padding=2, fmt="%d")
                    ax.grid(axis="y", alpha=0.25)

            # Hide any leftover axes
            for j in range(n_attrs, len(axes)):
                axes[j].set_visible(False)
            plt.tight_layout()
            # If nothing visible on this figure (all axes hidden) skip showing it
            visible_axes = [a for a in axes if a.get_visible()]
            if visible_axes:
                plt.show()
            else:
                plt.close(fig)
        if not any_plotted:
            warnings.warn(
                "No attribute distributions contained data (check agent objects / attribute names).",
                RuntimeWarning,
            )
        return results

    def _analyze_correlations(self) -> Dict[str, Any]:
        """Compute correlations among numerical attributes (age, memory sizes, counts, etc.)."""
        numeric_fields = [
            "age",
            "episodic_memory_size",
            "message_count",
            "stimuli_count",
            "social_connections",
        ]
        rows: List[Dict[str, Union[int, float]]] = []
        for agent in self.agents:
            row: Dict[str, Union[int, float]] = {}
            has_any = False
            # Access via agent.get if available; otherwise getattr or dict
            for f in numeric_fields:
                val = None
                if hasattr(agent, "get") and callable(getattr(agent, "get")):
                    try:
                        val = agent.get(f)
                    except Exception:
                        val = None
                elif isinstance(agent, dict):
                    val = agent.get(f)
                else:
                    val = getattr(agent, f, None)
                if isinstance(val, (int, float)):
                    row[f] = val
                    has_any = True
            if has_any:
                rows.append(row)
        if not rows:
            return {}
        df = pd.DataFrame(rows)
        # Drop columns with constant values
        df = df.loc[:, df.nunique() > 1]
        if df.shape[1] < 2:
            return {
                "available_fields": list(df.columns),
                "note": "Not enough variable fields for correlation.",
            }
        correlation_matrix = df.corr(numeric_only=True)
        # Collect strong correlations
        strong: List[Dict[str, Union[str, float]]] = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) >= 0.4:
                    strong.append(
                        {
                            "pair": (
                                correlation_matrix.columns[i],
                                correlation_matrix.columns[j],
                            ),
                            "correlation": float(corr_value),
                        }
                    )
        return {
            "available_fields": list(correlation_matrix.columns),
            "correlation_matrix": correlation_matrix.to_dict(),
            "strong_correlations": strong,
        }

    def _plot_advanced_analysis(self) -> None:
        """Create advanced visualizations for the analysis results."""

        # 1. Demographics overview
        if "demographics" in self.analysis_results:
            self._plot_demographics()

        # 2. Persona composition (new panel)
        if "persona_composition" in self.analysis_results:
            # Use defaults (show_empty False, include extra facets True)
            self._plot_persona_composition()

        # 3. Correlation heatmap
        if (
            "correlations" in self.analysis_results
            and "correlation_matrix" in self.analysis_results["correlations"]
        ):
            self._plot_correlation_heatmap()

    def _plot_demographics(self) -> Dict[str, pd.DataFrame]:
        """Plot demographic analysis results (age histogram, occupations, geography, diversity indices).

        Returns:
            Dict[str, DataFrame]: age, occupations, geography, diversity.
        """
        demo = self.analysis_results["demographics"]
        data_frames: Dict[str, pd.DataFrame] = {}

        fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
        fig.suptitle("Population Demographics", fontsize=16, fontweight="bold")

    # Age distribution (now accessed solely via agent.get('age'))
        if "age_stats" in demo:
            ages: List[Any] = []
            for agent in self.agents:
                val = None
                if hasattr(agent, "get") and callable(getattr(agent, "get")):
                    try:
                        val = agent.get("age")
                    except Exception:
                        val = None
                elif isinstance(agent, dict):
                    val = agent.get("age")
                if val is not None:
                    ages.append(val)
            sns.histplot(
                ages,
                bins=min(10, max(5, int(np.sqrt(len(ages))))),
                ax=axes[0, 0],
                color="steelblue",
                edgecolor="black",
            )
            axes[0, 0].axvline(
                demo["age_stats"]["mean"],
                color="red",
                linestyle="--",
                label=f"Mean: {demo['age_stats']['mean']:.1f}",
            )
            axes[0, 0].set_title("Age Distribution")
            axes[0, 0].set_xlabel("Age")
            axes[0, 0].legend()
            data_frames["age"] = pd.DataFrame({"age": ages})

        # Occupations
        if "occupation_diversity" in demo and demo["occupation_diversity"].get(
            "most_common"
        ):
            occ_data = demo["occupation_diversity"]["most_common"]
            occs, counts = zip(*occ_data)
            df_occ = pd.DataFrame({"occupation": occs, "count": counts})
            sns.barplot(
                data=df_occ, y="occupation", x="count", ax=axes[0, 1], palette="viridis"
            )
            axes[0, 1].set_title("Top Occupations")
            data_frames["occupations"] = df_occ

        # Geography
        if "geographic_diversity" in demo and demo["geographic_diversity"].get(
            "distribution"
        ):
            geo_data = demo["geographic_diversity"]["distribution"]
            geo_series = pd.Series(geo_data).sort_values(ascending=False)
            if len(geo_series) > self._top_n:
                top_geo = geo_series.head(self._top_n - 1)
                other_sum = geo_series.iloc[self._top_n - 1 :].sum()
                if other_sum > 0:
                    geo_series = pd.concat([top_geo, pd.Series({"Other": other_sum})])
                else:
                    geo_series = top_geo
            df_geo = geo_series.reset_index()
            df_geo.columns = ["country", "count"]
            sns.barplot(
                data=df_geo, y="country", x="count", ax=axes[1, 0], palette="magma"
            )
            axes[1, 0].set_title("Geographic Distribution (Top)")
            data_frames["geography"] = df_geo

        # Diversity indices
        diversity_rows = []
        if "occupation_diversity" in demo:
            diversity_rows.append(
                {
                    "metric": "Occupation Diversity",
                    "value": demo["occupation_diversity"]["diversity_index"],
                }
            )
        if "geographic_diversity" in demo:
            diversity_rows.append(
                {
                    "metric": "Geographic Diversity",
                    "value": demo["geographic_diversity"]["diversity_index"],
                }
            )
        if diversity_rows:
            df_div = pd.DataFrame(diversity_rows)
            sns.barplot(
                data=df_div, x="metric", y="value", ax=axes[1, 1], palette="Set2"
            )
            axes[1, 1].set_ylim(0, 1)
            axes[1, 1].set_title("Diversity Indices")
            axes[1, 1].tick_params(axis="x", rotation=20)
            for c in axes[1, 1].containers:
                axes[1, 1].bar_label(c, fmt="%.2f", padding=2)
            data_frames["diversity"] = df_div
        else:
            axes[1, 1].set_visible(False)

        plt.tight_layout(rect=(0, 0, 1, 0.97))
        plt.show()
        self.plot_data.update({f"demographics_{k}": v for k, v in data_frames.items()})
        return data_frames

    # (Removed legacy placeholder _plot_persona_composition definition; real implementation appears earlier.)

    def _plot_correlation_heatmap(self) -> pd.DataFrame:
        """Plot correlation heatmap for numerical attributes.
        if metric != "agent_proportion" and metric in plot_df.columns:
            for c in ax.containers:
                ax.bar_label(c, fontsize=7, padding=2, fmt="%d")
        """
        corr_data = self.analysis_results["correlations"]["correlation_matrix"]
        corr_df = pd.DataFrame(corr_data)
        plt.figure(figsize=(6.5, 5.5))
        sns.heatmap(
            corr_df,
            annot=True,
            cmap="coolwarm",
            center=0,
            fmt=".2f",
            linewidths=0.5,
            cbar_kws={"label": "Correlation"},
        )
        plt.title("Attribute Correlations", pad=10)
        plt.tight_layout()
        plt.show()
        self.plot_data["correlations"] = corr_df
        return corr_df

    def _compute_attributes_distributions(self, agents: list) -> dict:
        """
        Computes the distributions of the attributes for the agents.
        """
        distributions: Dict[str, pd.DataFrame] = {}
        empty_attrs: List[str] = []
        for attribute in self.attributes:
            dist = self._compute_attribute_distribution(agents, attribute)
            if dist is None or (hasattr(dist, "empty") and dist.empty) or len(dist) == 0:  # type: ignore[arg-type]
                empty_attrs.append(attribute)
            distributions[attribute] = dist

        # If every attribute ended up empty, attempt heuristic fallbacks once
        if empty_attrs and len(empty_attrs) == len(self.attributes) and agents:
            exemplar = (
                agents[0]
                if isinstance(agents[0], dict)
                else getattr(agents[0], "__dict__", {})
            )
            top_level_keys = (
                set(exemplar.keys()) if isinstance(exemplar, dict) else set()
            )
            recovered: Dict[str, pd.DataFrame] = {}
            for attribute in empty_attrs:
                # Only try heuristic if dotted path
                if "." not in attribute:
                    continue
                keys = attribute.split(".")
                candidates = [keys[-1], keys[0], attribute.replace(".", "_")]
                for cand in candidates:
                    if cand in top_level_keys:
                        dist = self._compute_attribute_distribution(agents, cand)
                        if dist is not None and len(dist) > 0:  # type: ignore[arg-type]
                            distributions[attribute] = dist
                            recovered[attribute] = dist
                            break
            if recovered:
                warnings.warn(
                    "Heuristic attribute fallback used for: "
                    + ", ".join(f"'{k}'" for k in recovered.keys())
                    + ". Consider updating Profiler(attributes=...) to direct keys.",
                    RuntimeWarning,
                )
        # Final diagnostics if still all empty
        if agents and all((hasattr(v, "empty") and v.empty) or len(v) == 0 for v in distributions.values()):  # type: ignore[arg-type]
            # Attempt brute-force recovery: search recursively for keys matching requested attribute names
            recovered_any = False
            for attr in list(distributions.keys()):
                if distributions[attr] is not None and not (
                    hasattr(distributions[attr], "empty") and distributions[attr].empty
                ):
                    continue  # already has data
                collected = self._brute_force_collect_attribute(agents, attr)
                if collected:
                    try:
                        recovered_series = (
                            pd.Series(collected).value_counts().sort_index()
                        )
                        distributions[attr] = recovered_series
                        recovered_any = True
                        warnings.warn(
                            f"Brute-force recovered values for attribute '{attr}'. Consider specifying explicit path.",
                            RuntimeWarning,
                        )
                    except Exception:
                        pass
            if recovered_any:
                return distributions
            # Provide path suggestions for user
            suggestions = self._suggest_attribute_paths(agents[:5], max_depth=3)
            exemplar = (
                agents[0]
                if isinstance(agents[0], dict)
                else getattr(agents[0], "__dict__", {})
            )
            try:
                exemplar_keys = (
                    list(exemplar.keys())[:50] if isinstance(exemplar, dict) else []
                )
            except Exception:
                exemplar_keys = []
            warnings.warn(
                "All attribute distributions are empty. Top-level keys: "
                + ", ".join(exemplar_keys)
                + (
                    " | Suggested nested paths: " + ", ".join(suggestions[:25])
                    if suggestions
                    else ""
                ),
                RuntimeWarning,
            )
        return distributions

    def _compute_attribute_distribution(
        self, agents: list, attribute: str
    ) -> pd.DataFrame:
        """Compute the distribution of a given attribute with support for nested attributes.
        
        Args:
            agents: List of agents (TinyPerson or dict)
            attribute: Attribute path (supports dot notation)
            
        Returns:
            Series with value counts or empty DataFrame if no values found
        """
        values: List[Any] = []
        for agent in agents:
            value = self._get_nested_attribute(agent, attribute)
            values.append(value)

        # Handle None values
        values = [v for v in values if v is not None]

        if not values:
            return pd.DataFrame()

        # Convert mixed types to string for consistent sorting
        try:
            value_counts = pd.Series(values).value_counts().sort_index()
        except TypeError:
            # Handle mixed data types by converting to strings
            string_values = [str(v) for v in values]
            value_counts = pd.Series(string_values).value_counts().sort_index()

        return value_counts

    # ------------------------------------------------------------------
    # Attribute path inference utilities
    # ------------------------------------------------------------------
    def _infer_attribute_path(
        self, agents: List[dict], target_key: str
    ) -> Optional[str]:
        """Heuristically discover a nested path for a simple attribute name.

        Strategy:
          1. Depth-first search limited depth (3) & breadth (dicts up to 30 keys) on first few agents.
          2. Return first path whose final segment (case-insensitive) matches target_key.
        """
        max_depth = 3
        target_l = target_key.lower()

        def dfs(obj: Any, depth: int, prefix: str) -> Optional[str]:
            if depth > max_depth:
                return None
            if isinstance(obj, dict):
                for k, v in list(obj.items())[:50]:  # breadth limit
                    new_path = f"{prefix}.{k}" if prefix else k
                    if k.lower() == target_l:
                        return new_path
                    if isinstance(v, dict):
                        found = dfs(v, depth + 1, new_path)
                        if found:
                            return found
            return None

        for agent in agents[:10]:
            if not isinstance(agent, dict):
                continue
            found = dfs(agent, 0, "")
            if found:
                warnings.warn(
                    f"Inferred path '{found}' for attribute '{target_key}'. Update Profiler(attributes=[...]) for efficiency.",
                    RuntimeWarning,
                )
                return found
        return None

    def _brute_force_collect_attribute(
        self, agents: List[dict], target_key: str
    ) -> List[Any]:
        """Recursively collect all values whose key matches the target_key (case-insensitive). Limited depth and breadth.

        Args:
            agents: list of agent dicts
            target_key: attribute name requested (simple)
        Returns:
            List of collected primitive values (excluding dict/list containers)
        """
        target_l = target_key.lower()
        results: List[Any] = []
        max_depth = 4

        def walk(obj: Any, depth: int) -> None:
            if depth > max_depth:
                return
            if isinstance(obj, dict):
                for k, v in list(obj.items())[:80]:  # breadth cap
                    if k.lower() == target_l and not isinstance(v, (dict, list)):
                        results.append(v)
                    walk(v, depth + 1)
            elif isinstance(obj, list):
                for it in obj[:80]:
                    walk(it, depth + 1)

        for ag in agents[:30]:
            if isinstance(ag, dict):
                walk(ag, 0)
        return results

    def _suggest_attribute_paths(
        self, agents: List[dict], max_depth: int = 3
    ) -> List[str]:
        paths: List[str] = []
        seen: set = set()

        def walk(obj: Any, depth: int, prefix: str):
            if depth > max_depth:
                return
            if isinstance(obj, dict):
                for k, v in list(obj.items())[:50]:
                    new_path = f"{prefix}.{k}" if prefix else k
                    if new_path not in seen:
                        seen.add(new_path)
                        paths.append(new_path)
                    walk(v, depth + 1, new_path)
            elif isinstance(obj, list):
                for it in obj[:20]:
                    walk(it, depth + 1, prefix)

        for ag in agents:
            if isinstance(ag, dict):
                walk(ag, 0, "")
        return paths

    def _get_nested_attribute(self, agent: dict, attribute: str) -> Any:
        """Get attribute from agent supporting both TinyPerson.get() and dict traversal.

        For TinyPerson objects (non-dict with .get() method), uses their .get() which supports
        dot notation. For plain dicts, performs manual dot-path traversal.
        
        Args:
            agent: TinyPerson instance or dict
            attribute: Attribute path (supports dot notation like "occupation.title")
            
        Returns:
            Attribute value or None if not found
        """
        # Check if it's a TinyPerson (has .get() but is NOT a plain dict)
        if hasattr(agent, "get") and callable(getattr(agent, "get")) and not isinstance(agent, dict):
            try:
                return agent.get(attribute)
            except Exception:
                return None
        # Fallback: simple dict dot traversal (for plain dicts)
        if not isinstance(agent, dict):
            return None
        cur: Any = agent
        for seg in attribute.split('.'):
            if isinstance(cur, dict) and seg in cur:
                cur = cur[seg]
            else:
                return None
        return cur

    # Utility methods for advanced analysis
    def _test_normality(self, data: List[float]) -> bool:
        """Simple normality test using skewness."""
        if len(data) < 3:
            return False

        skewness = pd.Series(data).skew()
        return (
            abs(skewness) < 0.3
        )  # Stringent normality test - threshold to catch bimodal distributions

    def _calculate_diversity_index(self, counts: Counter) -> float:
        """Calculate Shannon diversity index."""
        total = sum(counts.values())
        if total <= 1:
            return 0.0

        diversity = 0
        for count in counts.values():
            if count > 0:
                p = count / total
                diversity -= p * np.log(p)

        return diversity / np.log(len(counts)) if len(counts) > 1 else 0

    def _categorize_connectivity(self, connections: List[int]) -> Dict[str, int]:
        """Categorize agents by their connectivity level."""
        categories = {"isolated": 0, "low": 0, "medium": 0, "high": 0}

        for conn in connections:
            if conn == 0:
                categories["isolated"] += 1
            elif conn <= 2:
                categories["low"] += 1
            elif conn <= 5:
                categories["medium"] += 1
            else:
                categories["high"] += 1

        return categories

    def _identify_dominant_traits(self, traits_df: pd.DataFrame) -> Dict[str, str]:
        """Identify the dominant personality traits in the population."""
        trait_means = traits_df.mean()
        dominant = {}

        for trait, mean_value in trait_means.items():
            if mean_value > 0.6:
                dominant[trait] = "high"
            elif mean_value < 0.4:
                dominant[trait] = "low"
            else:
                dominant[trait] = "moderate"

        return dominant

    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive summary statistics."""
        summary = {
            "total_agents": len(self.agents),
            "attributes_analyzed": len(self.attributes),
            "data_completeness": {},
        }

        # Calculate data completeness for each attribute - handle empty data
        if len(self.agents) > 0:
            for attr in self.attributes:
                non_null_count = sum(
                    1
                    for agent in self.agents
                    if self._get_nested_attribute(agent, attr) is not None
                )
                summary["data_completeness"][attr] = non_null_count / len(self.agents)
        else:
            # No agents - set all completeness to 0
            for attr in self.attributes:
                summary["data_completeness"][attr] = 0.0

        return summary

    def export_analysis_report(
        self, filename: str = "agent_population_analysis.txt"
    ) -> None:
        """Export a comprehensive text report of the analysis."""
        with open(filename, "w", encoding="utf-8", errors="replace") as f:
            f.write("AGENT POPULATION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")

            # Summary statistics - always generate from current data
            summary = self._generate_summary_statistics()
            f.write(f"Total Agents Analyzed: {summary['total_agents']}\n")
            f.write(f"Attributes Analyzed: {summary['attributes_analyzed']}\n\n")

            f.write("Data Completeness:\n")
            for attr, completeness in summary["data_completeness"].items():
                f.write(f"  {attr}: {completeness:.2%}\n")
            f.write("\n")

            # Demographics
            if "demographics" in self.analysis_results:
                demo = self.analysis_results["demographics"]
                f.write("DEMOGRAPHICS\n")
                f.write("-" * 20 + "\n")

                if "age_stats" in demo:
                    age_stats = demo["age_stats"]
                    f.write(f"Age Statistics:\n")
                    f.write(f"  Mean: {age_stats['mean']:.1f} years\n")
                    f.write(f"  Median: {age_stats['median']:.1f} years\n")
                    f.write(
                        f"  Range: {age_stats['min']}-{age_stats['max']} years\n\n"
                    )

                if "occupation_diversity" in demo:
                    occ_div = demo["occupation_diversity"]
                    f.write(f"Occupation Diversity:\n")
                    f.write(f"  Unique Occupations: {occ_div['total_unique']}\n")
                    f.write(f"  Diversity Index: {occ_div['diversity_index']:.3f}\n\n")

            # Persona composition summary
            if "persona_composition" in self.analysis_results:
                comp = self.analysis_results["persona_composition"]
                f.write("PERSONA COMPOSITION (Top Facets)\n")
                f.write("-" * 30 + "\n")
                for facet_key in [
                    "interests",
                    "skills",
                    "beliefs",
                    "goals",
                    "likes_dislikes",
                    "communication_style",
                ]:
                    if (
                        facet_key in comp
                        and isinstance(comp[facet_key], pd.DataFrame)
                        and not comp[facet_key].empty
                    ):
                        top = comp[facet_key].head(5)
                        f.write(f"{facet_key.title()}:\n")
                        for _, row in top.iterrows():
                            if facet_key == "likes_dislikes":
                                f.write(
                                    f"  - {row['category']}: net={row['net_score']} (likes={row['likes']}, dislikes={row['dislikes']})\n"
                                )
                            else:
                                f.write(f"  - {row['category']} ({row['count']})\n")
                        f.write("\n")

        print(f"Analysis report exported to {filename}")

    def add_custom_analysis(
        self, name: str, analysis_func: Callable[[List[Dict]], Any]
    ) -> None:
        """
        Add a custom analysis function that will be executed during profiling.

        Args:
            name: Name for the custom analysis
            analysis_func: Function that takes agent data and returns analysis results
        """
        if not hasattr(self, "_custom_analyses"):
            self._custom_analyses = {}

        self._custom_analyses[name] = analysis_func

    def compare_populations(
        self,
        other_agents: List[dict],
        attributes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compare this population with another population.

        Args:
            other_agents: Another set of agents to compare with
            attributes: Specific attributes to compare (uses self.attributes if None)

        Returns:
            Comparison results
        """
        if attributes is None:
            attributes = self.attributes

        # Create temporary profiler for the other population
        other_profiler = Profiler(attributes)
        other_results = other_profiler.profile(
            other_agents, plot=False, advanced_analysis=True
        )

        comparison = {
            "population_sizes": {
                "current": len(self.agents),
                "comparison": len(other_profiler.agents),
            },
            "attribute_comparisons": {},
        }

        # Compare distributions for each attribute
        for attr in attributes:
            if (
                attr in self.attributes_distributions
                and attr in other_profiler.attributes_distributions
            ):

                current_dist = self.attributes_distributions[attr]
                other_dist = other_profiler.attributes_distributions[attr]

                # Statistical comparison (simplified)
                comparison["attribute_comparisons"][attr] = {
                    "current_unique_values": len(current_dist),
                    "comparison_unique_values": len(other_dist),
                    "current_top_3": current_dist.head(3).to_dict(),
                    "comparison_top_3": other_dist.head(3).to_dict(),
                }

        return comparison
