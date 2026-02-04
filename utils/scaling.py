import pandas as pd

def manual_min_max_scaling(df, columns):
    df_scaled = df.copy()
    for col in columns:
        col_min = df[col].min()
        col_max = df[col].max()
        
        # Avoid division by zero if all values are the same
        if col_max - col_min != 0:
            df_scaled[col] = (df[col] - col_min) / (col_max - col_min)
        else:
            df_scaled[col] = 0
            
    return df_scaled

def percentile_scaling(df, columns):
    df_scaled = df.copy()
    for col in columns:
        # We define the 95th percentile as the "max" (1.0)
        # and the 5th percentile as the "min" (0.0)
        upper_limit = df[col].quantile(0.95)
        lower_limit = df[col].quantile(0.05)
        
        # Scale the data and "clip" it so values don't go above 1 or below 0
        df_scaled[col] = (df[col] - lower_limit) / (upper_limit - lower_limit)
        df_scaled[col] = df_scaled[col].clip(0, 1)
            
    return df_scaled