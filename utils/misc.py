import pandas as pd
from datetime import datetime
import yahoo_fin.stock_info as si


def get_price_data(ticker):
    # Get historical price data from yahoo_fin
    df = si.get_data(ticker)
    # Change date from index to column
    df.reset_index(inplace=True)
    # Change column name to 'date'
    df = df.rename(columns={'index': 'date'})
    return(df)


def del_unnamed_col(dataframe):
    '''
    Delete any column with header 'Unnamed'
    '''
    dataframe.drop(dataframe.filter(regex='Unnamed').columns, axis=1, inplace=True)
    return dataframe

def str2date(date_string):
    '''
    Change date in string format to datetime format
    '''
    if '-' in date_string:
        datetime_object = datetime.strptime(date_string, '%Y-%m-%d')
    elif '/' in date_string:
        datetime_object = datetime.strptime(date_string, '%d/%m/%Y')
    
    return pd.to_datetime(datetime_object)

def clean_df(dataframe):
    '''
    Clean up dataframe from csv. Delete 'Unnamed' columns and convert dates from string format to datetime format.
    '''
    dataframe = del_unnamed_col(dataframe)
    dataframe.reset_index(drop=True)
    dataframe['date'] = dataframe.apply(lambda x: str2date(x['date']), axis=1)
    return dataframe


def date2str(datetime_obj):
    day = datetime_obj.day
    month = datetime_obj.month
    year = datetime_obj.year
    
    return str(day) + '/' + str(month) + '/' + str(year)


def get_attr(args, key=None, default_value=None):
    '''
    If args is a dict: return args[key]
    If args is an object: return args.key

    If args[key] or args.key is not found, return default value
    '''
    if isinstance(args, dict):
        return args[key] if key in args else default_value
    elif isinstance(args, object):
        return getattr(args, key, default_value) if key is not None else default_value
    

def annualise_returns(total_return, num_days=None, num_trading_days=None):
    '''
    Calculate annualised returns from total_return
    '''
    assert num_days != None or num_trading_days != None, 'Time period required'
    if num_days != None:
        return total_return ** (365.25 / num_days)
    else:
        return total_return ** (252 / num_trading_days)