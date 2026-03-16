# 시계열 데이터 시간패턴 제거 방법 (Time Series Deseasonalization)

좋은 질문이야.\
**"평균을 빼라"는 건 그냥 임의로 하는 게 아니라 시계열 분석에서 정식
방법론이 있음.**\
핵심은 **시계열 분해(time series decomposition)** 또는 **계절성
제거(deseasonalization)**다.

------------------------------------------------------------------------

# 1️⃣ 시계열 기본 모델

시계열 데이터는 보통 이렇게 분해된다고 가정한다.

## Additive 모델

Y_t = T_t + S_t + R_t

-   Y_t : 실제값\
-   T_t : 추세 (trend)\
-   S_t : 계절성 (seasonality)\
-   R_t : 잔차 (residual)

즉

데이터 = 장기추세 + 반복패턴 + 랜덤

**평균을 빼는 것 = S_t 제거 과정**이다.

------------------------------------------------------------------------

# 2️⃣ 어떤 평균을 빼냐 (핵심)

주 / 월 / 계절마다 패턴이 다르기 때문에 **주기(period)** 를 먼저 정해야
한다.

## 따릉이 데이터 기준

  패턴        주기
  ----------- --------
  시간 패턴   24시간
  요일 패턴   7일
  연간 패턴   365일

그래서 보통 **시간 + 요일 패턴을 같이 제거**한다.

``` python
df['seasonal_mean'] = df.groupby(['weekday','hour'])['rental_count'].transform('mean')
df['target'] = df['rental_count'] - df['seasonal_mean']
```

이 과정이 바로 **계절성 제거 (Deseasonalization)** 이다.

------------------------------------------------------------------------

# 3️⃣ 정식 방법들

## ① Classical Decomposition

전통적인 방식

Y = Trend + Seasonality + Residual

``` python
from statsmodels.tsa.seasonal import seasonal_decompose

result = seasonal_decompose(df['rental_count'], period=24)
```

결과

-   trend
-   seasonal
-   resid

------------------------------------------------------------------------

## ② STL Decomposition

STL = Seasonal Trend decomposition using LOESS

장점

-   복잡한 패턴 처리 가능
-   노이즈 강함

``` python
from statsmodels.tsa.seasonal import STL

stl = STL(df['rental_count'], period=24)
result = stl.fit()

trend = result.trend
seasonal = result.seasonal
resid = result.resid
```

모델 학습은 보통

residual

을 사용한다.

------------------------------------------------------------------------

## ③ Fourier Seasonality

계절성을 **sin / cos 함수**로 표현하는 방법

``` python
import numpy as np

df['sin_hour'] = np.sin(2*np.pi*df['hour']/24)
df['cos_hour'] = np.cos(2*np.pi*df['hour']/24)
```

이 방식은

-   Prophet
-   SARIMA
-   Deep Learning

에서 많이 사용된다.

------------------------------------------------------------------------

# 4️⃣ 따릉이 데이터에서 실제로 쓰는 방식

``` python
df['seasonal_mean'] = df.groupby(
    ['station_id','weekday','hour']
)['rental_count'].transform('mean')

df['target'] = df['rental_count'] - df['seasonal_mean']
```

이유

-   대여소마다 패턴 다름
-   평일 / 주말 패턴 다름
-   시간 패턴 매우 강함

------------------------------------------------------------------------

# 5️⃣ 중요한 포인트

평균을 빼는 목적

모델이 시간 패턴을 외우는 것을 방지

즉

모델이 학습해야 하는 것

-   날씨
-   이벤트
-   교통
-   지역 특성

------------------------------------------------------------------------

# 6️⃣ 실무에서 많이 사용하는 조합

수요예측에서는 보통

1.  시간 + 요일 평균 제거\
2.  Time-based split\
3.  Lag feature 추가

조합을 사용한다.

------------------------------------------------------------------------

# 참고

데이터가 매우 클 경우 (예: 400만 행)

다음 원인 때문에 점수가 비정상적으로 높아질 수 있다.

1.  return_count 사용\
2.  net_flow 사용\
3.  random train/test split

이 경우 **데이터 누수 (Data Leakage)** 가 발생할 수 있다.
