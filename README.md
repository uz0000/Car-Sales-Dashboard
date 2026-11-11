# Car-Sales-Dashboard
 Dashboard showing which listing details are related to the price of a used car and how long it takes to sell

 # Link to the app
https://car-sales-dashboard-oh6p.onrender.com

 # What the dashboard shows
 - What drives price: price against mileage and age, and median price by condition, vehicle type, 4wd and cylinders
 - Depreciation: how fast each condition loses value as the cars get older
 - What drives time to sell: days listed against price, condition and paint color
 - Correlations: how the numeric columns relate to each other

 # What was found
 - Age and mileage had the strongest relationship with price, older and higher mileage cars were cheaper
 - Cars in better condition had higher prices, but they were also newer
 - Days listed was not related to price, condition or color, most cars took about 33 days to sell

 # Notes
 - Cars listed for under $500 (mostly $1) were treated as placeholder prices and filtered out, this can be changed in the sidebar
 - The full analysis is in notebooks/EDA.ipynb
