library(dplyr)
library(tidyr)
library(jsonlite)
library(lubridate)
library(naniar)

# Load data
apo_data <- fromJSON('https://raw.githubusercontent.com/crcorbett/scraping/main/Data/apo.json')
apo_data <- tbl_df(apo_data$decisions)

apo_data$datetime <- ymd(apo_data$datetime)

# Create statistics
decisions_month_current <- apo_data %>% 
  filter(year(datetime)==year(now(tzone="Australia/Melbourne"))) %>% 
  group_by(month=floor_date(datetime, "month")) %>% 
  count(month)

months <- apo_data %>% 
  filter(year(datetime)=='2020') %>% 
  group_by(month=floor_date(datetime, "month")) %>% 
  count() %>% 
  select(month)

mean <- apo_data %>% 
  filter(year(datetime)!=year(now(tzone="Australia/Melbourne"))) %>% 
  group_by(month=floor_date(datetime, "month")) %>% 
  count(month) %>% 
  group_by(month(month)) %>% 
  summarise(mean=mean(n)) %>%
  select(mean)

decisions_month_avg$month <- months$month
decisions_month_avg$n <- mean$mean

miss_rep <- apo_data %>% filter(applicant_pa=='' | applicant_counsel=='' | opponent_pa=='' | opponent_counsel=='')

fortnight <- interval(date(now())-weeks(2), now())
year <- interval(date(now())-years(1), now())

miss_rep_14 <- miss_rep %>% filter(datetime %within% fortnight) %>% count()

miss_rep_ann <- miss_rep %>% filter(datetime %within% year) %>% count()

decisions_14 <- apo_data %>% filter(datetime %within% fortnight) %>% count()

decisions_ann <- apo_data %>% filter(datetime %within% year) %>% count()

apo_data <- apo_data %>% replace_with_na_all(condition=~.x %in% c(""))

top_counsel <- apo_data %>%
  select(opponent_counsel, applicant_counsel) %>% 
  gather(key = "Type", value = "Counsel") %>% 
  drop_na() %>% 
  group_by(Counsel) %>% 
  count(sort=T) %>%
  ungroup() %>%
  slice_head()

top_pa <- apo_data %>%
  select(opponent_pa, applicant_pa) %>% 
  gather(key = "Type", value = "PA") %>% 
  drop_na() %>% 
  group_by(PA) %>% 
  count(sort=T) %>%
  ungroup() %>%
  slice_head()


# Create JSON
body <- list()
body$miss_rep_14 <- miss_rep_14$n
body$miss_rep_ann <- miss_rep_ann$n
body$decisions_14 <- decisions_14$n
body$decisions_ann <- decisions_ann$n
body$top_counsel <- top_counsel$Counsel
body$top_pa <- top_pa$PA

decisions_month_current_body <- list()
decisions_month_current_body$month <- decisions_month_current$month
decisions_month_current_body$n <- decisions_month_current$n

decisions_month_avg_body <- list()
decisions_month_avg_body$month <- decisions_month_avg$month
decisions_month_avg_body$n <- decisions_month_avg$n

body$decisions_month_current <- decisions_month_current_body
body$decisions_month_avg <- decisions_month_avg_body

apo_stats <- toJSON(body, pretty = T)

write(apo_stats, "Data/APO_stats.json")
