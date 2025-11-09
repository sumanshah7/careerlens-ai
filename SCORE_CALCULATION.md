# Overall Score Calculation

## Overview
The Overall Score (0-100) is a comprehensive assessment of your resume's career readiness. It's calculated using a weighted combination of three key metrics.

## Score Formula

```
Overall Score = (Domain Score × 50%) + (Skills Score × 30%) + (Balance Score × 20%)
```

**Final Score is capped at 95** to leave room for improvement.

## Metrics Breakdown

### 1. Domain Score (50% weight)
- **What it measures**: How well your resume matches your primary career domain
- **Calculation**: 
  - Uses the **top domain's confidence score** from the AI analysis
  - Domain score ranges from 0.0 to 1.0 (from AI analysis)
  - Converted to 0-100 scale: `Math.round(topDomain.score * 100)`
- **Example**: 
  - If your top domain is "AI Engineer" with a score of 0.9
  - Domain Score = 0.9 × 100 = **90 points**
  - Weighted contribution = 90 × 0.5 = **45 points**

### 2. Skills Score (30% weight)
- **What it measures**: The breadth and depth of your technical skills
- **Calculation**:
  - Counts total skills across all categories: `core + adjacent + advanced`
  - Normalized to 100%: `(totalSkills / 10) * 100`
  - 10+ skills = 100%, 5 skills = 50%, 0 skills = 0%
- **Example**:
  - If you have 8 total skills (5 core + 2 adjacent + 1 advanced)
  - Skills Score = (8 / 10) × 100 = **80 points**
  - Weighted contribution = 80 × 0.3 = **24 points**

### 3. Balance Score (20% weight)
- **What it measures**: The balance between your strengths and areas for growth
- **Calculation**:
  - Formula: `(strengthsCount / (strengthsCount + weaknessesCount)) × 100`
  - More strengths than weaknesses = higher score
  - If no weaknesses: 100 points (if strengths exist) or 50 points (if no strengths)
- **Example**:
  - If you have 4 strengths and 2 areas for growth
  - Balance Score = (4 / (4 + 2)) × 100 = **66.67 points**
  - Weighted contribution = 66.67 × 0.2 = **13.33 points**

## Complete Example Calculation

Let's say your resume analysis shows:
- **Top Domain**: "AI Engineer" with score 0.9 (90%)
- **Skills**: 8 total skills (5 core + 2 adjacent + 1 advanced)
- **Strengths**: 4 items
- **Areas for Growth**: 2 items

### Step-by-step calculation:

1. **Domain Score**: 0.9 × 100 = 90 points
   - Weighted: 90 × 0.5 = **45 points**

2. **Skills Score**: (8 / 10) × 100 = 80 points
   - Weighted: 80 × 0.3 = **24 points**

3. **Balance Score**: (4 / (4 + 2)) × 100 = 66.67 points
   - Weighted: 66.67 × 0.2 = **13.33 points**

4. **Total Score**: 45 + 24 + 13.33 = **82.33 points**
   - Rounded: **82 points**
   - Capped at 95: **82 points** (final)

## Score Interpretation

- **90-95**: Excellent - Strong match with minimal gaps
- **80-89**: Very Good - Strong skills with some areas to improve
- **70-79**: Good - Solid foundation with room for growth
- **60-69**: Fair - Some skills but significant gaps to address
- **Below 60**: Needs Improvement - Focus on building core skills

## How to Improve Your Score

### To increase Domain Score (50% weight):
- Ensure your resume clearly demonstrates expertise in your target role
- Use role-specific keywords and technologies
- Highlight relevant projects and experiences

### To increase Skills Score (30% weight):
- Add more technical skills (aim for 10+ total)
- Balance between core, adjacent, and advanced skills
- Include both technical and soft skills

### To increase Balance Score (20% weight):
- Add more strengths to your resume
- Address areas for growth by learning new skills
- Show continuous improvement and learning

## Technical Details

**Location**: `frontend/src/store/useAppStore.ts` (lines 121-153)

**Code Reference**:
```typescript
// Domain Score (50% weight)
const domainScore = topDomain 
  ? Math.round(topDomain.score * 100)
  : 50;

// Skills Score (30% weight)
const skillsCount = (analysis.skills.core?.length || 0) + 
                   (analysis.skills.adjacent?.length || 0) + 
                   (analysis.skills.advanced?.length || 0);
const skillsScore = Math.min(100, Math.max(0, (skillsCount / 10) * 100));

// Balance Score (20% weight)
const balanceScore = weaknessesCount > 0 
  ? Math.min(100, Math.max(0, (strengthsCount / (strengthsCount + weaknessesCount)) * 100))
  : strengthsCount > 0 ? 100 : 50;

// Weighted composite score
const currentScore = Math.round(
  domainScore * 0.5 + 
  skillsScore * 0.3 + 
  balanceScore * 0.2
);

// Cap at 95
const finalScore = Math.min(95, Math.max(0, currentScore));
```

## Notes

- The score is **dynamic** and recalculated each time you analyze your resume
- The score is **capped at 95** to encourage continuous improvement
- The score is **stored in the analysis object** for display and tracking
- The score is **compared with previous versions** to track progress over time

