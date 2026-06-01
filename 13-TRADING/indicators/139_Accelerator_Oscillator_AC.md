# Indicator 139: Accelerator Oscillator (AC) — The Early Warning System

***"Price is the last element to change. Before price changes, momentum changes. Before momentum changes, acceleration changes. The Accelerator Oscillator is the first thing to move." — Bill Williams***

---

## 1. Executive Summary

The **Accelerator Oscillator (AC)** handles the third derivative of price action.

1. Price (Distance)
2. AO (Velocity/Momentum)
3. AC (Acceleration/Deceleration)

If the Awesome Oscillator (AO) measures the speed of the price movement, the Accelerator Oscillator (AC) measures **how fast that speed is changing**. Just as a car must decelerate before it can reverse, the market's momentum must decelerate before the trend can turn.

The AC is the **earliest warning signal** in the Chaos framework. It often changes color *before* the AO turns, and significantly before price reverses.

Visually, it is a histogram centered around zero.

- **Green Bar**: Acceleration is increasing (Bullish).
- **Red Bar**: Acceleration is decreasing (Bearish).

In GOLIATH, the AC acts as a **Predictive Filter**. It allows the system to exit positions early (when acceleration dies) rather than waiting for momentum to actually reverse (which is often too late).

---

## 2. Mathematical Foundations

The AC is derived directly from the Awesome Oscillator (AO).

$$ \text{AC} = \text{AO} - SMA(\text{AO}, 5) $$

This formula is conceptually identical to the MACD Histogram (which is MACD Line - Signal Line). Here, the AO is the "Line" and the SMA(AO, 5) is the "Signal Line". By subtracting the signal line from the indicator, we isolate the **raw change in momentum**.

### 2.1 The Zero Line

Unlike AO, the Zero Line in AC is not a major trading signal. The AC oscillates around zero, but because it is so sensitive, crossing zero happens frequently.

- **Zero Cross**: Indicates that momentum is now equal to its average.
- **Ideally**: We wan to buy when AC is positive (accelerating up) and AO is positive (moving up).

---

## 3. Signal Generation

### 3.1 Buying with AC

You cannot buy on a Red bar. You need **two consecutive Green bars** to buy if AC is above zero, or **three consecutive Green bars** if AC is below zero.

**Type 1: Above Zero Buy**

- Condition: AC > 0.
- Signal: Red Bar -> Green Bar -> Green Bar.
- Action: Buy Stop 1 tick above the High of the second Green bar.

**Type 2: Below Zero Buy**

- Condition: AC < 0.
- Signal: Red Bar -> Green Bar -> Green Bar -> Green Bar.
- Action: Buy Stop 1 tick above the High of the third Green bar.
- *Why 3 bars?* Because fighting negative acceleration requires more proof of reversal.

### 3.2 Selling with AC

Mirror image of buying.

**Type 1: Below Zero Sell**

- Condition: AC < 0.
- Signal: Green Bar -> Red Bar -> Red Bar.
- Action: Sell Stop 1 tick below Low.

**Type 2: Above Zero Sell**

- Condition: AC > 0.
- Signal: Green Bar -> Red Bar -> Red Bar -> Red Bar.
- Action: Sell Stop 1 tick below Low.

---

## 4. Implementation

### 4.1 Python Implementation

```python
import pandas as pd

def compute_accelerator_oscillator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Bill Williams' Accelerator Oscillator (AC).
    AO = SMA(Median, 5) - SMA(Median, 34)
    AC = AO - SMA(AO, 5)
    """
    if 'ao' not in df.columns:
        from .awesome_oscillator_ao import compute_awesome_oscillator
        df = compute_awesome_oscillator(df)
        
    df = df.copy()
    
    # 1. Get AO
    ao = df['ao']
    
    # 2. SMA(AO, 5)
    sma_ao_5 = ao.rolling(window=5).mean()
    
    # 3. AC
    df['ac'] = ao - sma_ao_5
    
    # 4. Color Coding (1=Green, -1=Red)
    df['ac_color'] = 0
    df.loc[df['ac'] > df['ac'].shift(1), 'ac_color'] = 1
    df.loc[df['ac'] <= df['ac'].shift(1), 'ac_color'] = -1
    
    return df
```

### 4.2 Rust Implementation

```rust
pub struct AcceleratorOscillator {
    ao_calc: AwesomeOscillator,
    buffer_ao: VecDeque<f64>,
    sum_ao: f64,
    prev_ac: f64,
}

impl AcceleratorOscillator {
    pub fn new() -> Self {
        Self {
            ao_calc: AwesomeOscillator::new(),
            buffer_ao: VecDeque::with_capacity(5),
            sum_ao: 0.0,
            prev_ac: 0.0,
        }
    }

    pub fn next(&mut self, high: f64, low: f64) -> (f64, bool) {
        // 1. Get AO
        let (ao_val, _) = self.ao_calc.next(high, low);
        
        // 2. Update SMA of AO
        self.buffer_ao.push_back(ao_val);
        self.sum_ao += ao_val;
        if self.buffer_ao.len() > 5 {
            self.sum_ao -= self.buffer_ao.pop_front().unwrap();
        }
        
        // 3. Calculate AC
        let sma_ao = if self.buffer_ao.len() == 5 { 
            self.sum_ao / 5.0 
        } else { 
            0.0 // Not ready 
        };
        
        let ac = ao_val - sma_ao;
        
        // 4. Color
        let is_green = ac > self.prev_ac;
        self.prev_ac = ac;
        
        (ac, is_green)
    }
}
```

---

## 5. Strategy: The Zone Trading

In GOLIATH, AC is primarily used for **Zone Trading**.

- **Green Zone**: Both AO and AC are Green. This is a "Aggressive" state. The system allows adding positions on any setup.
- **Red Zone**: Both AO and AC are Red. Aggressive Shorting permitted.
- **Grey Zone**: AO and AC are different colors. The market is in transition. Reduce risk. Take profits on existing positions but do not enter new ones.

This **Color Match Filter** drastically reduces drawdown during choppy transitions.

---

## Reference Statistics

| Property | Value |
|---|---|
| Indicator ID | 139 |
| Name | Accelerator Oscillator (AC) |
| Author | Bill Williams |
| Formula | AO - SMA(AO, 5) |
| Output | Histogram |
| Type | Leading Indicator |
| GOLIATH Role | Early Warning / Zone Trading Filter |
| Colors | Green (Increasing), Red (Decreasing) |
