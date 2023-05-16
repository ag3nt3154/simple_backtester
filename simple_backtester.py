import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from trade_obj import trade, tradeList
from utils import misc

class backTester:
    def __init__(self, **kwargs) -> None:
        self.df = None
        self.initial_capital = misc.get_attr(kwargs, 'initial_capital', 1E6)
        self.reward_function = misc.get_attr(kwargs, 'reward_function', None)
        self.mode = misc.get_attr(kwargs, 'mode', 'trading')
        self.per_order_fees = misc.get_attr(kwargs, 'per_order_fees', 0)
        self.per_volume_fees = misc.get_attr(kwargs, 'per_volume_fees', 0)
        
        self.clean_slate()

        


    def clean_slate(self):
        '''
        Set initial default state of environment.
        Called by __init__ and reset
        '''
        # State variables
        self.cash = self.initial_capital
        self.position = 0
        self.position_value = 0
        self.portfolio_value = self.cash + self.position_value
        self.leverage = abs(self.position_value / self.portfolio_value)
        self.portfolio_volatility = 0
        self.portfolio_return = 1
        self.end = False
        self.current_step = 0
        self.open_trade = None

        # record all instantaneous values of state
        self.record = {
            'cash': [],
            'position': [],
            'position_value': [],
            'portfolio_value': [],
            'leverage': [],
        }

        # record all trades
        self.trade_record = tradeList()

        # instantaneous state of the trader
        self.trader_state = np.array([
            self.cash,
            self.position,
            self.position_value,
            self.portfolio_value,
            # self.leverage,
        ])



    def set_asset(self, df):
        self.df = df

        self.open = self.df['open'].to_numpy()
        self.high = self.df['high'].to_numpy()
        self.low = self.df['low'].to_numpy()
        self.close = self.df['close'].to_numpy()
        self.adjclose = self.df['adjclose'].to_numpy()
        self.date = self.df.index.to_list()



    def take_action(self, order_quantity=0, order_price=0, order_type='market_on_close'):
        execution_price = 0
        execution_quantity = 0
        # price at which to evaluate position
        evaluation_price = self.adjclose[self.current_step]
        if order_quantity == 0:
            pass
        else:
            # execute based on order type
            if order_type == 'market_on_close':
                execution_price = self.adjclose[self.current_step]
                execution_quantity = order_quantity
            
            if self.mode == 'trading':
                # record trades
                if self.open_trade == None:
                    assert self.position == 0, 'no open trades but position != 0'
                    # opening new trade
                    cost_basis = execution_price + self.per_volume_fees + (self.per_order_fees / execution_quantity)
                    self.open_trade = trade(self.date[self.current_step], cost_basis, execution_quantity)
                else:
                    # close trade
                    self.open_trade.close(self.date[self.current_step], execution_price)
                    self.trade_record.append(self.open_trade)
                    self.open_trade = None

            elif self.mode == 'portfolio_optimisation':
                pass
                
            
            self.position += execution_quantity
            self.cash -= (execution_price * execution_quantity)
            self.cash -= (self.per_order_fees + self.per_volume_fees * execution_quantity)

        # calculate new trader state
        self.position_value = self.position * evaluation_price
        self.portfolio_value = self.cash + self.position_value
        self.leverage = abs(self.position_value / self.portfolio_value)

        self.trader_state = np.array([
            self.cash,
            self.position,
            self.position_value,
            self.portfolio_value,
            # self.leverage,
            # self.portfolio_volatility,
        ])

        # record
        self.record['cash'].append(self.cash)
        self.record['position'].append(self.position)
        self.record['position_value'].append(self.position_value)
        self.record['portfolio_value'].append(self.portfolio_value)
        self.record['leverage'].append(self.leverage)

        self.current_step += 1

        if self.current_step == len(self.df):
            print('end')


    def analyse(self):
        self.records = pd.DataFrame.from_dict(self.record)
        self.records['date'] = self.date
        self.records = self.records.set_index('date')
        self.records['returns'] = self.records['portfolio_value'].pct_change()
        self.records['cum_returns'] = (self.records['portfolio_value'] 
                                              / self.records['portfolio_value'][0])
        self.records['drawdown'] = (self.records['cum_returns'] - self.records['cum_returns'].cummax())/self.records['cum_returns'].cummax()
        self.records['buy_hold_returns'] = self.df['adjclose'].pct_change()
        self.records['buy_hold_cum_returns'] = self.adjclose / self.adjclose[0]
        self.records['buy_hold_drawdown'] = (self.records['buy_hold_cum_returns'] - self.records['buy_hold_cum_returns'].cummax())/self.records['buy_hold_cum_returns'].cummax()
        
        self.time_period = (self.date[-1] - self.date[0]).days
        self.annual_return = self.records['cum_returns'][-1] ** (365.25/self.time_period) - 1
        self.annual_vol = self.records['returns'].std() * np.sqrt(252)
        
        self.buy_hold_annual_return = self.records['buy_hold_cum_returns'][-1] ** (365.25/self.time_period) - 1
        self.buy_hold_annual_vol = self.records['buy_hold_returns'].std() * np.sqrt(252)
        print(f'Annualised return: {self.annual_return}')
        print(f'buy_hold annual return: {self.buy_hold_annual_return}')
        print(f'Annualised vol: {self.annual_vol}')
        print(f'buy_hold annual vol: {self.buy_hold_annual_vol}')
        print(f'Sharpe ratio: {self.annual_return / self.annual_vol}')
        print(f'buy_hold Sharpe ratio: {self.buy_hold_annual_return / self.buy_hold_annual_vol}')
        
        

        


    def plot_graphs(self):
        fig, axs = plt.subplots(4, 2, figsize=(16, 14))
        axs[0, 0].plot(self.records['cum_returns'], label='strategy')
        axs[0, 0].set_title('Cumulative returns')
        axs[0, 0].legend()

        axs[0, 1].plot(self.records['buy_hold_cum_returns'], label='buy_hold', color='C1')
        axs[0, 1].plot(self.records['cum_returns'], label='strategy')
        axs[0, 1].set_title('Cumulative returns')
        axs[0, 1].legend()

        axs[1, 0].hist(self.records['returns'], bins=50, label='strategy')
        axs[1, 0].set_title('Daily returns')
        axs[1, 0].legend()

        axs[1, 1].hist(self.records['buy_hold_returns'], bins=50, label='buy_hold', color='C1')
        axs[1, 1].hist(self.records['returns'], bins=50, label='strategy')
        axs[1, 1].set_title('Daily returns')
        axs[1, 1].legend()
        

        axs[2, 0].plot(self.records['drawdown'], label='strategy')
        axs[2, 0].set_title('Drawdown')
        axs[2, 0].legend()

        axs[2, 1].plot(self.records['buy_hold_drawdown'], label='buy_hold', color='C1')
        axs[2, 1].plot(self.records['drawdown'], label='strategy')
        axs[2, 1].set_title('Drawdown')
        axs[2, 1].legend()

        axs[3, 0].hist(self.records['drawdown'], label='strategy', bins=50)
        axs[3, 0].set_title('Drawdown')
        axs[3, 0].legend()

        axs[3, 1].hist(self.records['buy_hold_drawdown'], label='buy_hold', color='C1', bins=50)
        axs[3, 1].hist(self.records['drawdown'], label='strategy', bins=50)
        axs[3, 1].set_title('Drawdown')
        axs[3, 1].legend()





