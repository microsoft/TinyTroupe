# 🔧 SURGICAL ASYNC FIX PLAN
*Blake's immediate fix for epic simulation launch*

**Status**: Addressed. Use `return_actions=True` when calling `listen_and_act` or `act` in scripts.
See `listen_and_act` and `act` docstrings in `tinytroupe/agent/tiny_person.py`.

## 🚨 **PROBLEM IDENTIFIED**
```
RuntimeWarning: coroutine 'TinyPerson.listen_and_act' was never awaited
```

## 🔧 **SURGICAL FIX OPTIONS**

### **OPTION 1: Use return_actions parameter**
```python
# CURRENT (BROKEN):
response = agent.listen_and_act(crisis_prompt)

# FIX 1 (TRY FIRST):
response = agent.listen_and_act(crisis_prompt, return_actions=True)
```

### **OPTION 2: Async wrapper**
```python
# FIX 2 (IF OPTION 1 FAILS):
import asyncio
response = asyncio.run(agent.listen_and_act(crisis_prompt))
```

### **OPTION 3: Check for sync version**
```python
# FIX 3 (INVESTIGATE):
# Look for listen_and_act_sync or similar method
response = agent.listen_and_act_sync(crisis_prompt)
```

## ⚡ **IMMEDIATE ACTION**
1. Try Option 1 first (most likely to work)
2. Test with single agent
3. Scale to full 20-agent simulation
4. Collect metrics and results

## 📊 **SUCCESS METRICS**
- ✅ No coroutine warnings
- ✅ Agent responses generated
- ✅ 20 agents complete crisis simulation
- ✅ Results saved to epic_simulation_results.json
- ✅ Cache optimization maintained