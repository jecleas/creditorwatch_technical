# %% IMPORTING PACKAGES

import pandas as pd
import matplotlib.pyplot as plt

# %%
## read xyz-billing file initially
xyz_billing = pd.read_csv(r"xyz-billing.csv", 
                          parse_dates = True,
                          #index_col = 1
                          )

#ensure date time 
xyz_billing.date = pd.to_datetime(xyz_billing.date)

# %%
#do for the physical calendar purchases and monthly purchases first

#xyz_billing['month'] = xyz_billing.index.month
xyz_billing_month = xyz_billing\
                    .loc[xyz_billing["itemDescription"]
                                    .isin(["calendar purchase",
                                           "monthly subscription"])]

#new cols for month and year
xyz_billing_month = xyz_billing_month\
                    .assign(month = xyz_billing_month.date.dt.month,
                            year = xyz_billing_month.date.dt.year,
                            MRR = xyz_billing_month.amount
                            )

#aggregate by year and month

xyz_physical_month_MRR = xyz_billing_month\
                            .groupby(["year","month"])\
                                .agg({'MRR':'sum'})
# %%

#do for the annual calendar purchases
xyz_billing_annually = xyz_billing\
                        .loc[xyz_billing["itemDescription"] == "annual subscription"]

#create list of dfs and concat together
#in each list item offset month further by 1
#also add column MRR by dividing amount by 12
annual_list = [xyz_billing_annually\
                         .assign(date = 
                                 xyz_billing_annually['date'] + 
                                 pd.DateOffset(months=i),
                                 MRR = xyz_billing_annually['amount'] / 12
                                 ) for i in range(1,13)]

xyz_billing_annual = pd.concat(annual_list)

xyz_billing_annual = xyz_billing_annual\
                    .assign(month = xyz_billing_annual.date.dt.month,
                            year = xyz_billing_annual.date.dt.year
                            ) 

xyz_annual_MRR = xyz_billing_annual\
                            .groupby(["year","month"])\
                                .agg({'MRR':'sum'})

# %%
#concatenate the two MRR tables together

xyz_MRR = pd.concat([xyz_annual_MRR, xyz_physical_month_MRR]).sort_index()
xyz_MRR = xyz_MRR.reset_index().groupby(["year","month"]).sum() #reaggregate

# %% #QUESTION 1

xyz_MRR.plot(kind="line", title = "XYZ MRR over months", ylabel = "MRR")
plt.show()
print(xyz_MRR)
# %% QUESTION 2

xyz_payment_schedule = pd.concat([xyz_billing_annual,xyz_billing_month])\
                        .sort_values("date")

# %%
xyz_growth = xyz_payment_schedule\
                .pivot_table(values = "MRR", 
                             index = ["year","month"], 
                             columns = "itemDescription",
                             margins = True)

xyz_growth_pct = xyz_growth.pct_change().drop("All")

xyz_growth_pct.plot(kind="line", 
                    title = "MRR Change per Month (%)", 
                    ylabel = "MRR change from previous month (%)")
plt.show()
print(xyz_growth_pct)

# %% QUESTION 3
#create new dataframe to reindex in case any months/years are not accounted for in data and replace with 0
#create new index (make sure all months in the calendar are accounted for)

date_reindex = pd.DataFrame({"date": pd.date_range(min(xyz_payment_schedule.date),
                                                    max(xyz_payment_schedule.date), 
                                                    freq = 'M')})
date_reindex = date_reindex.assign(month = date_reindex.date.dt.month, 
                                  year = date_reindex.date.dt.year)\
                                  .drop("date", axis = 1)

#create pivot per customer - the ones starting with 0s are months where they have churned
xyz_customer = xyz_payment_schedule.pivot_table(values = "MRR",
                                                index = ["year","month"],
                                                columns = "customerID")

#reindex capture all dates
xyz_customer = xyz_customer\
                .reindex([date_reindex.year,date_reindex.month],fill_value = 0)\
                        .fillna(0)

def check_customer(x):
    return((x.shift(1) != 0) & (x == 0))

xyz_churn = xyz_customer.apply(check_customer, axis = 0).loc[(2021,12):(2022,3),:]
xyz_churn = xyz_churn.sum(axis = 1)

print(xyz_customer)

xyz_churn.plot(kind = "bar", title = "Churn Customers per Month for Dec 2021 to March 2022")
plt.show()

print(xyz_churn)
