# 私有参考解析（不得传执行者）

以下全部来自官方CSV真实记录；没有改造观测值。模型始终只用2011-01-01至2011-09-30训练。

| 指标 | 2011 Q4 | 2012全年 |
|---|---:|---:|
| hours | 2203 | 8734 |
| days | 92 | 366 |
| C0_MAE | 58.825190495 | 118.118276200 |
| C1_MAE | 44.570832408 | 108.708121500 |
| C0_RMSE | 86.080568956 | 174.111341077 |
| C1_RMSE | 67.999969061 | 157.211075359 |
| C0_bias_prediction_minus_actual | 1.078965172 | -91.533693613 |
| C1_bias_prediction_minus_actual | 0.987153116 | -91.613465374 |
| MAE_reduction_absolute | 14.254358087 | 9.410154700 |
| MAE_reduction_fraction | 0.242317245 | 0.079667220 |
| C0_day_equal_weight_MAE | 58.848612995 | 117.775867403 |
| C1_day_equal_weight_MAE | 44.620153798 | 108.360746461 |
| day_equal_weight_MAE_reduction_fraction | 0.241780706 | 0.079941003 |

2011整年数据核验：{"absent_calendar_hour_slots": 115, "blank_cell_count_day": 0, "blank_cell_count_hour": 0, "cnt_identity_violations_day": 0, "cnt_identity_violations_hour": 0, "cnt_total_day": 1243103, "cnt_total_hour": 1243103, "daily_mean_count": 3405.7616438356163, "day_rows": 365, "duplicate_date_hour_pairs": 0, "full24_dates": 305, "hour_rows": 8645, "hour_to_day_cnt_disagreement_dates": 0, "hours_per_date_frequency": {"8": 1, "12": 1, "16": 1, "17": 1, "18": 2, "22": 6, "23": 48, "24": 305}, "leaky_casual_plus_registered_MAE": 0, "rare_partial_dates": [{"cnt": 683, "date": "2011-01-18", "hours": 12}, {"cnt": 506, "date": "2011-01-26", "hours": 16}, {"cnt": 431, "date": "2011-01-27", "hours": 8}, {"cnt": 4334, "date": "2011-08-28", "hours": 17}], "unique_dates_hour": 365}

2012整年数据核验：{"absent_calendar_hour_slots": 50, "blank_cell_count_day": 0, "blank_cell_count_hour": 0, "cnt_identity_violations_day": 0, "cnt_identity_violations_hour": 0, "cnt_total_day": 2049576, "cnt_total_hour": 2049576, "daily_mean_count": 5599.934426229508, "day_rows": 366, "duplicate_date_hour_pairs": 0, "full24_dates": 350, "hour_rows": 8734, "hour_to_day_cnt_disagreement_dates": 0, "hours_per_date_frequency": {"1": 1, "11": 1, "23": 14, "24": 350}, "leaky_casual_plus_registered_MAE": 0, "rare_partial_dates": [{"cnt": 22, "date": "2012-10-29", "hours": 1}, {"cnt": 1096, "date": "2012-10-30", "hours": 11}], "unique_dates_hour": 366}

年度总计增长=64.875798706945%；每日日计数均值增长=64.425318382610%。2011为365天，2012为366天，所以分母不同。

## phase1 依赖与敏感性

{
  "bootstrap7": {
    "B": 2000,
    "absolute_difference_percentile95": [
      10.800923355912134,
      17.57808163043943
    ],
    "block_days": 7,
    "interpretation": "dependence-sensitive exploratory interval; requires suitable within-period stability",
    "method": "paired circular moving blocks of dates; pooled hourly metric",
    "relative_reduction_percentile95": [
      0.17071940679252828,
      0.3148328823524697
    ],
    "seed": 20261029
  },
  "bootstrap28": {
    "B": 2000,
    "absolute_difference_percentile95": [
      9.815819623823897,
      18.33421270659497
    ],
    "block_days": 28,
    "interpretation": "dependence-sensitive exploratory interval; requires suitable within-period stability",
    "method": "paired circular moving blocks of dates; pooled hourly metric",
    "relative_reduction_percentile95": [
      0.15571346410314052,
      0.325449081470458
    ],
    "seed": 20261029
  },
  "full24_dates_sensitivity": {
    "C0_MAE": 58.255512218176314,
    "C0_RMSE": 85.46995638895247,
    "C0_bias_prediction_minus_actual": -1.9402373790969094,
    "C0_day_equal_weight_MAE": 58.255512218176314,
    "C1_MAE": 43.37124548933945,
    "C1_RMSE": 66.34386467313968,
    "C1_bias_prediction_minus_actual": -2.0303810549520045,
    "C1_day_equal_weight_MAE": 43.37124548933945,
    "MAE_reduction_absolute": 14.884266728836863,
    "MAE_reduction_fraction": 0.25549971431189,
    "day_equal_weight_MAE_reduction_fraction": 0.25549971431189,
    "day_equal_weight_mean_MAE_difference": 14.884266728836867,
    "days": 87,
    "hours": 2088
  },
  "subgroups": {
    "weathersit=1": {
      "C0_MAE": 58.80325688038747,
      "C0_RMSE": 87.69133457060975,
      "C0_bias_prediction_minus_actual": -7.926581252192282,
      "C0_day_equal_weight_MAE": 54.59707699899897,
      "C1_MAE": 43.11865871324888,
      "C1_RMSE": 65.98744340877063,
      "C1_bias_prediction_minus_actual": -8.171108374759806,
      "C1_day_equal_weight_MAE": 40.22588724032208,
      "MAE_reduction_absolute": 15.684598167138596,
      "MAE_reduction_fraction": 0.26673009284235494,
      "day_equal_weight_MAE_reduction_fraction": 0.26322269521755504,
      "day_equal_weight_mean_MAE_difference": 14.371189758676893,
      "days": 86,
      "hours": 1437
    },
    "weathersit=2": {
      "C0_MAE": 48.079183332577784,
      "C0_RMSE": 70.0290821976623,
      "C0_bias_prediction_minus_actual": -7.7361572733406785,
      "C0_day_equal_weight_MAE": 46.610317456236174,
      "C1_MAE": 34.07477350138013,
      "C1_RMSE": 51.09891303133159,
      "C1_bias_prediction_minus_actual": -6.142198421245389,
      "C1_day_equal_weight_MAE": 33.3996338943293,
      "MAE_reduction_absolute": 14.004409831197655,
      "MAE_reduction_fraction": 0.29127803054234624,
      "day_equal_weight_MAE_reduction_fraction": 0.28342831121694856,
      "day_equal_weight_mean_MAE_difference": 13.210683561906878,
      "days": 63,
      "hours": 531
    },
    "weathersit=3": {
      "C0_MAE": 83.24071562849058,
      "C0_RMSE": 106.58467873767934,
      "C0_bias_prediction_minus_actual": 76.06534912749318,
      "C0_day_equal_weight_MAE": 76.08193075897388,
      "C1_MAE": 77.16734678136602,
      "C1_RMSE": 104.02493083927703,
      "C1_bias_prediction_minus_actual": 73.09824855187225,
      "C1_day_equal_weight_MAE": 64.28227118948583,
      "MAE_reduction_absolute": 6.073368847124556,
      "MAE_reduction_fraction": 0.07296151650389993,
      "day_equal_weight_MAE_reduction_fraction": 0.155091484295649,
      "day_equal_weight_mean_MAE_difference": 11.799659569488057,
      "days": 31,
      "hours": 235
    },
    "workingday=0": {
      "C0_MAE": 81.15601440711939,
      "C0_RMSE": 109.2968064715611,
      "C0_bias_prediction_minus_actual": 6.291172350904274,
      "C0_day_equal_weight_MAE": 81.21663142660834,
      "C1_MAE": 50.62625069904984,
      "C1_RMSE": 74.70678158635515,
      "C1_bias_prediction_minus_actual": 5.5110235687153475,
      "C1_day_equal_weight_MAE": 50.766035692985085,
      "MAE_reduction_absolute": 30.529763708069545,
      "MAE_reduction_fraction": 0.37618608960904476,
      "day_equal_weight_MAE_reduction_fraction": 0.37493054315038954,
      "day_equal_weight_mean_MAE_difference": 30.450595733623256,
      "days": 31,
      "hours": 742
    },
    "workingday=1": {
      "C0_MAE": 47.48400545470794,
      "C0_RMSE": 71.45765762651197,
      "C0_bias_prediction_minus_actual": -1.568165373685341,
      "C0_day_equal_weight_MAE": 47.48125936511604,
      "C1_MAE": 41.49545912053218,
      "C1_RMSE": 64.32657600992741,
      "C1_bias_prediction_minus_actual": -1.3103909476440487,
      "C1_day_equal_weight_MAE": 41.496836769152964,
      "MAE_reduction_absolute": 5.9885463341757585,
      "MAE_reduction_fraction": 0.12611712674255893,
      "day_equal_weight_MAE_reduction_fraction": 0.1260375709486713,
      "day_equal_weight_mean_MAE_difference": 5.984422595963078,
      "days": 61,
      "hours": 1461
    }
  }
}

## phase2 依赖与敏感性

{
  "bootstrap7": {
    "B": 2000,
    "absolute_difference_percentile95": [
      8.083961388811415,
      10.825502808133027
    ],
    "block_days": 7,
    "interpretation": "dependence-sensitive exploratory interval; requires suitable within-period stability",
    "method": "paired circular moving blocks of dates; pooled hourly metric",
    "relative_reduction_percentile95": [
      0.06476413180843947,
      0.09967438859012907
    ],
    "seed": 20261029
  },
  "bootstrap28": {
    "B": 2000,
    "absolute_difference_percentile95": [
      7.667939814729397,
      11.466770540309206
    ],
    "block_days": 28,
    "interpretation": "dependence-sensitive exploratory interval; requires suitable within-period stability",
    "method": "paired circular moving blocks of dates; pooled hourly metric",
    "relative_reduction_percentile95": [
      0.057098410348891446,
      0.11589625362630877
    ],
    "seed": 20261029
  },
  "full24_dates_sensitivity": {
    "C0_MAE": 119.73153807694625,
    "C0_RMSE": 176.15551073192114,
    "C0_bias_prediction_minus_actual": -95.13925215742204,
    "C0_day_equal_weight_MAE": 119.73153807694625,
    "C1_MAE": 110.420108391637,
    "C1_RMSE": 159.1104439662443,
    "C1_bias_prediction_minus_actual": -95.21599113080177,
    "C1_day_equal_weight_MAE": 110.420108391637,
    "MAE_reduction_absolute": 9.31142968530925,
    "MAE_reduction_fraction": 0.07776923135594571,
    "day_equal_weight_MAE_reduction_fraction": 0.07776923135594571,
    "day_equal_weight_mean_MAE_difference": 9.311429685309255,
    "days": 350,
    "hours": 8400
  },
  "subgroups": {
    "weathersit=1": {
      "C0_MAE": 127.55365848642849,
      "C0_RMSE": 186.20487440438905,
      "C0_bias_prediction_minus_actual": -108.89798886828258,
      "C0_day_equal_weight_MAE": 120.97437535965207,
      "C1_MAE": 118.41496635380533,
      "C1_RMSE": 168.65041780473717,
      "C1_bias_prediction_minus_actual": -108.71774268505392,
      "C1_day_equal_weight_MAE": 111.97181690129257,
      "MAE_reduction_absolute": 9.138692132623163,
      "MAE_reduction_fraction": 0.0716458645017658,
      "day_equal_weight_MAE_reduction_fraction": 0.07441706916522817,
      "day_equal_weight_mean_MAE_difference": 9.002558458359504,
      "days": 356,
      "hours": 5768
    },
    "weathersit=2": {
      "C0_MAE": 102.35810261505502,
      "C0_RMSE": 152.44545009247966,
      "C0_bias_prediction_minus_actual": -76.25564844631167,
      "C0_day_equal_weight_MAE": 97.89733828014529,
      "C1_MAE": 92.70065404900397,
      "C1_RMSE": 136.06469468283373,
      "C1_bias_prediction_minus_actual": -77.14528355738739,
      "C1_day_equal_weight_MAE": 89.03391021994034,
      "MAE_reduction_absolute": 9.657448566051045,
      "MAE_reduction_fraction": 0.09434962469332264,
      "day_equal_weight_MAE_reduction_fraction": 0.09053798822232695,
      "day_equal_weight_mean_MAE_difference": 8.863428060204955,
      "days": 286,
      "hours": 2326
    },
    "weathersit=3": {
      "C0_MAE": 90.37753631971286,
      "C0_RMSE": 129.48344322457066,
      "C0_bias_prediction_minus_actual": 9.19945255231869,
      "C0_day_equal_weight_MAE": 89.24187141916487,
      "C1_MAE": 79.27342946089345,
      "C1_RMSE": 116.75761095654128,
      "C1_bias_prediction_minus_actual": 9.609443333824427,
      "C1_day_equal_weight_MAE": 78.59028576577623,
      "MAE_reduction_absolute": 11.104106858819407,
      "MAE_reduction_fraction": 0.12286357109291346,
      "day_equal_weight_MAE_reduction_fraction": 0.11935636808151007,
      "day_equal_weight_mean_MAE_difference": 10.651585653388638,
      "days": 151,
      "hours": 638
    },
    "weathersit=4": {
      "C0_MAE": 84.85366525307043,
      "C0_RMSE": 117.27900665946834,
      "C0_bias_prediction_minus_actual": 84.85366525307043,
      "C0_day_equal_weight_MAE": 84.85366525307043,
      "C1_MAE": 120.51896949500127,
      "C1_RMSE": 149.2350513983788,
      "C1_bias_prediction_minus_actual": 120.51896949500127,
      "C1_day_equal_weight_MAE": 120.51896949500127,
      "MAE_reduction_absolute": -35.66530424193084,
      "MAE_reduction_fraction": -0.4203154234476665,
      "day_equal_weight_MAE_reduction_fraction": -0.4203154234476665,
      "day_equal_weight_mean_MAE_difference": -35.66530424193084,
      "days": 2,
      "hours": 2
    },
    "workingday=0": {
      "C0_MAE": 127.79515436169565,
      "C0_RMSE": 180.7607778469249,
      "C0_bias_prediction_minus_actual": -77.61185682825932,
      "C0_day_equal_weight_MAE": 127.73314599464052,
      "C1_MAE": 105.54742684421791,
      "C1_RMSE": 153.24457464118237,
      "C1_bias_prediction_minus_actual": -78.39138747102314,
      "C1_day_equal_weight_MAE": 105.49027918177995,
      "MAE_reduction_absolute": 22.247727517477742,
      "MAE_reduction_fraction": 0.17408897566264925,
      "day_equal_weight_MAE_reduction_fraction": 0.17413543399137643,
      "day_equal_weight_mean_MAE_difference": 22.242866812860573,
      "days": 116,
      "hours": 2780
    },
    "workingday=1": {
      "C0_MAE": 113.60001599081399,
      "C0_RMSE": 170.9180640499784,
      "C0_bias_prediction_minus_actual": -98.03398018759295,
      "C0_day_equal_weight_MAE": 113.1556901370039,
      "C1_MAE": 110.1838909228832,
      "C1_RMSE": 159.02920931705486,
      "C1_bias_prediction_minus_actual": -97.78702542936846,
      "C1_day_equal_weight_MAE": 109.69264327801247,
      "MAE_reduction_absolute": 3.4161250679307926,
      "MAE_reduction_fraction": 0.030071519252312662,
      "day_equal_weight_MAE_reduction_fraction": 0.030604266164596106,
      "day_equal_weight_mean_MAE_difference": 3.4630468589914334,
      "days": 250,
      "hours": 5954
    }
  }
}

## 必须保留的解释

2011留出期相对改善24.2317%，7/28日块区间均在10%以上，但这不构成跨年性能保证。2012点改善7.96672%，仍改善且未达预设10%实务门槛；7日块上限约9.96744%，28日块区间跨10%，因此对“总体改善必定低于10%”的统计断言不稳健。冻结模型C1在2012平均低估约91.61辆/已观察小时。记录的是observed-hour表现，缺少的小时不能当零，不应对完整日历小时误差作无证据保证。

当前官网17,389实例 vs 原README17,379小时，原件实数支持后者；README season标签1:springer/2:summer/3:fall/4:winter与当前官网1:winter/2:spring/3:summer/4:fall冲突；温度README除41而官网小时范围47加偏移冲突。本任务预测模型不使用这些变量，故保留原编码并披露冲突即可，不需擅自解决为物理温度。

casual+registered=cnt在所有记录恒成立，零MAE是标签分解泄漏；随机小时拆分没有回答未来时间外推；历史同小时天气并非此前一日可用实测。workingday关联不是操控工作安排的因果效果。2012低计数/缺小时日期可以指出，不能无独立来源把它归因于飓风、停运或零需求。
