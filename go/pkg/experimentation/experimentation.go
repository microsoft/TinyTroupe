// Package experimentation provides experimental features and A/B testing capabilities.
// This module handles A/B testing framework, hypothesis testing, and statistical analysis.
package experimentation

import (
	"context"
	"fmt"
	"math"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/agent"
)

// ExperimentType represents different types of experiments
type ExperimentType string

const (
	ABTestExperiment         ExperimentType = "ab_test"
	MultiVariateExperiment   ExperimentType = "multivariate"
	HypothesisTestExperiment ExperimentType = "hypothesis_test"
	BehavioralExperiment     ExperimentType = "behavioral"
)

// ExperimentConfig defines the configuration for an experiment
type ExperimentConfig struct {
	Type         ExperimentType         `json:"type"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Duration     time.Duration          `json:"duration"`
	SampleSize   int                    `json:"sample_size"`
	Significance float64                `json:"significance"` // Alpha level (e.g., 0.05)
	Variables    map[string]interface{} `json:"variables"`
	Metrics      []string               `json:"metrics"`
	RandomSeed   int64                  `json:"random_seed,omitempty"`
}

// ExperimentResult contains the results of an experiment
type ExperimentResult struct {
	ExperimentID    string                 `json:"experiment_id"`
	Type            ExperimentType         `json:"type"`
	StartTime       time.Time              `json:"start_time"`
	EndTime         time.Time              `json:"end_time"`
	Duration        time.Duration          `json:"duration"`
	SampleSize      int                    `json:"sample_size"`
	Groups          map[string]*GroupData  `json:"groups"`
	Analysis        *StatisticalAnalysis   `json:"analysis"`
	Conclusion      string                 `json:"conclusion"`
	Significance    bool                   `json:"significance"`
	ConfidenceLevel float64                `json:"confidence_level"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// GroupData represents data for a single experimental group
type GroupData struct {
	Name          string                 `json:"name"`
	Size          int                    `json:"size"`
	Agents        []*agent.TinyPerson    `json:"-"` // Exclude from JSON
	Metrics       map[string][]float64   `json:"metrics"`
	Summary       map[string]float64     `json:"summary"`
	Interventions map[string]interface{} `json:"interventions"`
}

// StatisticalAnalysis contains statistical analysis results
type StatisticalAnalysis struct {
	Method           string             `json:"method"`
	PValue           float64            `json:"p_value"`
	TestStat         float64            `json:"test_statistic"`
	DegreesOfFreedom int                `json:"degrees_of_freedom,omitempty"`
	EffectSize       float64            `json:"effect_size"`
	PowerAnalysis    map[string]float64 `json:"power_analysis"`
	Recommendations  []string           `json:"recommendations"`
}

// Experiment interface defines experimentation capabilities
type Experiment interface {
	// Run executes the experiment
	Run(ctx context.Context) (*ExperimentResult, error)

	// Analyze analyzes the experiment results
	Analyze(result *ExperimentResult) (*StatisticalAnalysis, error)

	// GetConfig returns the experiment configuration
	GetConfig() *ExperimentConfig
}

// ExperimentRunner manages and executes experiments
type ExperimentRunner struct {
	experiments map[string]Experiment
	results     map[string]*ExperimentResult
}

// NewExperimentRunner creates a new experiment runner
func NewExperimentRunner() *ExperimentRunner {
	return &ExperimentRunner{
		experiments: make(map[string]Experiment),
		results:     make(map[string]*ExperimentResult),
	}
}

// RegisterExperiment registers an experiment with the runner
func (er *ExperimentRunner) RegisterExperiment(id string, experiment Experiment) {
	er.experiments[id] = experiment
}

// RunExperiment executes an experiment by ID
func (er *ExperimentRunner) RunExperiment(ctx context.Context, id string) (*ExperimentResult, error) {
	experiment, exists := er.experiments[id]
	if !exists {
		return nil, fmt.Errorf("experiment %s not found", id)
	}

	result, err := experiment.Run(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to run experiment %s: %w", id, err)
	}

	result.ExperimentID = id
	er.results[id] = result

	return result, nil
}

// GetResult retrieves a result by experiment ID
func (er *ExperimentRunner) GetResult(id string) (*ExperimentResult, bool) {
	result, exists := er.results[id]
	return result, exists
}

// ABTestExperimentImpl implements A/B testing functionality
type ABTestExperimentImpl struct {
	config         *ExperimentConfig
	controlGroup   *GroupData
	treatmentGroup *GroupData
}

// NewABTestExperiment creates a new A/B test experiment
func NewABTestExperiment(config *ExperimentConfig) *ABTestExperimentImpl {
	return &ABTestExperimentImpl{
		config: config,
		controlGroup: &GroupData{
			Name:          "control",
			Metrics:       make(map[string][]float64),
			Summary:       make(map[string]float64),
			Interventions: make(map[string]interface{}),
		},
		treatmentGroup: &GroupData{
			Name:          "treatment",
			Metrics:       make(map[string][]float64),
			Summary:       make(map[string]float64),
			Interventions: make(map[string]interface{}),
		},
	}
}

// GetConfig returns the experiment configuration
func (ab *ABTestExperimentImpl) GetConfig() *ExperimentConfig {
	return ab.config
}

// Run executes the A/B test experiment
func (ab *ABTestExperimentImpl) Run(ctx context.Context) (*ExperimentResult, error) {
	startTime := time.Now()

	// Initialize groups with equal sample sizes
	halfSize := ab.config.SampleSize / 2
	ab.controlGroup.Size = halfSize
	ab.treatmentGroup.Size = ab.config.SampleSize - halfSize

	// Simulate experiment data collection
	// In a real implementation, this would collect actual agent behavior data
	err := ab.collectMetrics(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to collect metrics: %w", err)
	}

	endTime := time.Now()

	result := &ExperimentResult{
		Type:       ab.config.Type,
		StartTime:  startTime,
		EndTime:    endTime,
		Duration:   endTime.Sub(startTime),
		SampleSize: ab.config.SampleSize,
		Groups: map[string]*GroupData{
			"control":   ab.controlGroup,
			"treatment": ab.treatmentGroup,
		},
		ConfidenceLevel: 1.0 - ab.config.Significance,
		Metadata:        make(map[string]interface{}),
	}

	// Perform statistical analysis
	analysis, err := ab.Analyze(result)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze results: %w", err)
	}

	result.Analysis = analysis
	result.Significance = analysis.PValue < ab.config.Significance
	result.Conclusion = ab.generateConclusion(analysis)

	return result, nil
}

// collectMetrics simulates metric collection for the experiment
func (ab *ABTestExperimentImpl) collectMetrics(ctx context.Context) error {
	// Generate synthetic data for demonstration
	// In a real implementation, this would interface with the actual agent simulation

	for _, metric := range ab.config.Metrics {
		// Control group baseline metrics
		controlData := ab.generateSyntheticMetric(metric, ab.controlGroup.Size, false)
		ab.controlGroup.Metrics[metric] = controlData
		ab.controlGroup.Summary[metric+"_mean"] = mean(controlData)
		ab.controlGroup.Summary[metric+"_std"] = stddev(controlData)

		// Treatment group metrics (with potential improvement)
		treatmentData := ab.generateSyntheticMetric(metric, ab.treatmentGroup.Size, true)
		ab.treatmentGroup.Metrics[metric] = treatmentData
		ab.treatmentGroup.Summary[metric+"_mean"] = mean(treatmentData)
		ab.treatmentGroup.Summary[metric+"_std"] = stddev(treatmentData)
	}

	return nil
}

// generateSyntheticMetric creates synthetic data for testing
func (ab *ABTestExperimentImpl) generateSyntheticMetric(metric string, size int, isTreatment bool) []float64 {
	data := make([]float64, size)

	// Base parameters that vary by metric type
	var baseMean, baseStd, treatmentEffect float64

	switch metric {
	case "engagement_score":
		baseMean, baseStd, treatmentEffect = 0.7, 0.15, 0.1
	case "task_completion_rate":
		baseMean, baseStd, treatmentEffect = 0.8, 0.12, 0.08
	case "response_time":
		baseMean, baseStd, treatmentEffect = 2.5, 0.8, -0.3 // Lower is better
	case "satisfaction_rating":
		baseMean, baseStd, treatmentEffect = 4.2, 0.6, 0.4
	default:
		baseMean, baseStd, treatmentEffect = 1.0, 0.2, 0.1
	}

	// Apply treatment effect
	if isTreatment {
		baseMean += treatmentEffect
	}

	// Generate normally distributed data
	for i := 0; i < size; i++ {
		// Simple Box-Muller transform for normal distribution
		u1 := math.Max(1e-10, float64(i+1)/float64(size+1))
		u2 := float64((i*7+13)%100) / 100.0

		z := math.Sqrt(-2*math.Log(u1)) * math.Cos(2*math.Pi*u2)
		data[i] = math.Max(0, baseMean+baseStd*z)
	}

	return data
}

// Analyze performs statistical analysis on the experiment results
func (ab *ABTestExperimentImpl) Analyze(result *ExperimentResult) (*StatisticalAnalysis, error) {
	if len(result.Groups) != 2 {
		return nil, fmt.Errorf("A/B test requires exactly 2 groups, got %d", len(result.Groups))
	}

	// Get control and treatment groups
	control := result.Groups["control"]
	treatment := result.Groups["treatment"]

	// Perform t-test on the primary metric (first metric)
	if len(ab.config.Metrics) == 0 {
		return nil, fmt.Errorf("no metrics specified for analysis")
	}

	primaryMetric := ab.config.Metrics[0]
	controlData := control.Metrics[primaryMetric]
	treatmentData := treatment.Metrics[primaryMetric]

	// Welch's t-test for unequal variances
	tStat, pValue, df := welchTTest(controlData, treatmentData)

	// Calculate effect size (Cohen's d)
	effectSize := cohensD(controlData, treatmentData)

	// Power analysis
	power := calculatePower(effectSize, float64(len(controlData)+len(treatmentData)), ab.config.Significance)

	analysis := &StatisticalAnalysis{
		Method:           "Welch's t-test",
		PValue:           pValue,
		TestStat:         tStat,
		DegreesOfFreedom: int(df),
		EffectSize:       effectSize,
		PowerAnalysis: map[string]float64{
			"power":       power,
			"sample_size": float64(len(controlData) + len(treatmentData)),
			"alpha":       ab.config.Significance,
		},
		Recommendations: ab.generateRecommendations(pValue, effectSize, power),
	}

	return analysis, nil
}

// generateConclusion creates a human-readable conclusion
func (ab *ABTestExperimentImpl) generateConclusion(analysis *StatisticalAnalysis) string {
	if analysis.PValue < ab.config.Significance {
		if analysis.EffectSize > 0 {
			return fmt.Sprintf("The treatment group showed a statistically significant improvement (p=%.4f, d=%.3f). The treatment should be implemented.",
				analysis.PValue, analysis.EffectSize)
		} else {
			return fmt.Sprintf("The treatment group showed a statistically significant decrease (p=%.4f, d=%.3f). The treatment should not be implemented.",
				analysis.PValue, analysis.EffectSize)
		}
	} else {
		return fmt.Sprintf("No statistically significant difference was found (p=%.4f). More data may be needed or the treatment may have no effect.",
			analysis.PValue)
	}
}

// generateRecommendations creates actionable recommendations
func (ab *ABTestExperimentImpl) generateRecommendations(pValue, effectSize, power float64) []string {
	var recommendations []string

	if pValue < ab.config.Significance {
		if math.Abs(effectSize) > 0.8 {
			recommendations = append(recommendations, "Large effect size detected - implement changes immediately")
		} else if math.Abs(effectSize) > 0.5 {
			recommendations = append(recommendations, "Medium effect size - consider gradual rollout")
		} else {
			recommendations = append(recommendations, "Small but significant effect - monitor closely during implementation")
		}
	} else {
		recommendations = append(recommendations, "No significant effect found - consider alternative approaches")
	}

	if power < 0.8 {
		recommendations = append(recommendations, fmt.Sprintf("Statistical power is low (%.2f) - consider increasing sample size", power))
	}

	if pValue > 0.05 && pValue < 0.1 {
		recommendations = append(recommendations, "Results are marginally significant - consider extending the experiment")
	}

	return recommendations
}

// Statistical helper functions

func mean(data []float64) float64 {
	sum := 0.0
	for _, v := range data {
		sum += v
	}
	return sum / float64(len(data))
}

func stddev(data []float64) float64 {
	m := mean(data)
	sum := 0.0
	for _, v := range data {
		sum += (v - m) * (v - m)
	}
	return math.Sqrt(sum / float64(len(data)-1))
}

func welchTTest(group1, group2 []float64) (tStat, pValue, df float64) {
	mean1, mean2 := mean(group1), mean(group2)
	std1, std2 := stddev(group1), stddev(group2)
	n1, n2 := float64(len(group1)), float64(len(group2))

	// Welch's t-test statistic
	se := math.Sqrt((std1*std1)/n1 + (std2*std2)/n2)
	tStat = (mean2 - mean1) / se

	// Welch-Satterthwaite degrees of freedom
	df = math.Pow((std1*std1)/n1+(std2*std2)/n2, 2) /
		(math.Pow((std1*std1)/n1, 2)/(n1-1) + math.Pow((std2*std2)/n2, 2)/(n2-1))

	// Approximate p-value using t-distribution (simplified)
	pValue = 2 * (1 - tCDF(math.Abs(tStat), df))

	return tStat, pValue, df
}

func cohensD(group1, group2 []float64) float64 {
	mean1, mean2 := mean(group1), mean(group2)
	std1, std2 := stddev(group1), stddev(group2)
	n1, n2 := float64(len(group1)), float64(len(group2))

	// Pooled standard deviation
	pooledStd := math.Sqrt(((n1-1)*std1*std1 + (n2-1)*std2*std2) / (n1 + n2 - 2))

	return (mean2 - mean1) / pooledStd
}

// Simplified t-CDF approximation
func tCDF(t, df float64) float64 {
	// Simplified approximation for demonstration
	// In a real implementation, use a proper statistical library
	x := t / math.Sqrt(df)
	return 0.5 + 0.5*math.Tanh(x*1.5)
}

// Simplified power calculation
func calculatePower(effectSize, sampleSize, alpha float64) float64 {
	// Simplified power calculation for demonstration
	// In a real implementation, use proper power analysis
	beta := math.Exp(-0.5 * effectSize * effectSize * sampleSize / 8)
	return math.Max(0, math.Min(1, 1-beta))
}
