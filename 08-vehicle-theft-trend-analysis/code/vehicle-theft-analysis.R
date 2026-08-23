# Kia & Hyundai Vehicle Theft Analysis: Municipal Public Safety Briefing
## "A Disproportionate Risk" — A Data-Driven Examination of Targeted Auto Theft Trends

# Kia & Hyundai Vehicle Theft Data
# **Objective:** Analyze Kia and Hyundai vehicle theft patterns to identify concentration, growth, and jurisdiction-level impact
# **Scenario:** Data analyst presenting findings to city officials and public safety leadership
# **Goal:** Support evidence-based, targeted prevention strategies rather than broad, unfocused policy responses
# **Data Sources:** 
#   - Kia Hyundai Milwaukee Data
#   - Kia Hyundai Thefts (multi-city)
#   - Car Thefts Map (2019–2022)
#   - Motherboard / VICE News Kia & Hyundai Theft Data
# **Audience:** City officials and public safety leadership
# **Medium:** PowerPoint (charts exported from R)
# **Call to Action:** Approve targeted prevention measures, including steering-wheel lock programs, focused patrol allocation, and localized public awareness efforts


# 0) Set data directory (your path)
data_dir <- "/Volumes/Extreme Pro/Box Sync/School/DSC/DSC 640/Week 5 - 6/Assignment/data"

# 1) Install packages (run once, then you can comment this block out)
pkgs <- c(
 "tidyverse", "readxl", "lubridate",
 "scales", "janitor",
 "treemapify" 
 )

to_install <- pkgs[!pkgs %in% installed.packages()[, "Package"]]
if (length(to_install) > 0) install.packages(to_install)

# 2) Load packages (run every session)
library(tidyverse)
library(readxl)
library(lubridate)
library(scales)
library(janitor)
library(treemapify)

# 3) Helper: safe file paths
csv_kia_hyundai_thefts <- file.path(data_dir, "kiaHyundaiThefts.csv")
csv_milwaukee          <- file.path(data_dir, "KiaHyundaiMilwaukeeData.csv")
csv_map                <- file.path(data_dir, "carTheftsMap.csv")
xlsx_vice              <- file.path(data_dir, "Motherboard VICE News Kia Hyundai Theft Data.xlsx")

# 4) Read the datasets
kia_thefts <- read_csv(csv_kia_hyundai_thefts, show_col_types = FALSE) |> clean_names()
milwaukee  <- read_csv(csv_milwaukee, show_col_types = FALSE) |> clean_names()
thefts_map <- read_csv(csv_map, show_col_types = FALSE) |> clean_names()

# VICE Excel: read first sheet by default, adjust if needed
vice_raw <- read_excel(xlsx_vice, sheet = 1) |> clean_names()

# 5) Print columns for reference
cat("\n=== kiaHyundaiThefts.csv columns ===\n"); print(names(kia_thefts))
cat("\n=== KiaHyundaiMilwaukeeData.csv columns ===\n"); print(names(milwaukee))
cat("\n=== carTheftsMap.csv columns ===\n"); print(names(thefts_map))
cat("\n=== Motherboard VICE Excel columns (raw) ===\n"); print(names(vice_raw))

# 6) Create an output folder for charts
out_dir <- file.path(data_dir, "../charts_out")
if (!dir.exists(out_dir)) dir.create(out_dir)

# ============================================================
# Data prep helpers
# ============================================================

# A) Standardize a month-year date if we have month + year columns
# This tries multiple common patterns, then falls back gracefully.
make_month_date <- function(df) {
  df |>
    mutate(
      month_clean = str_trim(as.character(month)),
      month_num = case_when(
        suppressWarnings(!is.na(as.integer(month_clean))) ~ as.integer(month_clean),
        month_clean %in% month.name ~ match(month_clean, month.name),
        month_clean %in% month.abb  ~ match(month_clean, month.abb),
        TRUE ~ NA_integer_
      ),
      month_date = as.Date(paste(year, month_num, "01", sep = "-"))
    ) |>
    filter(!is.na(month_date))
}

# B) Confirm expected columns exist, so I can catch mismatches early
require_cols <- function(df, cols, df_name = "dataframe") {
  missing <- setdiff(cols, names(df))
  if (length(missing) > 0) {
    stop(paste0(df_name, " is missing columns: ", paste(missing, collapse = ", ")))
  }
}

clean_city_label <- function(x) {
  x |>
    str_replace_all("_", " ") |>
    str_squish() |>
    str_to_title() |>
    # Fix common abbreviations like "D C" -> "DC"
    str_replace_all("\\bD C\\b", "DC") |>
    # Fix state abbreviations that get title-cased ("Wi" -> "WI")
    str_replace_all("\\b([A-Z][a-z])\\b", toupper) |>
    # Add comma before state abbreviations at end: "Milwaukee WI" -> "Milwaukee, WI"
    str_replace(" ([A-Z]{2})$", ", \\1")
}

# ============================================================
# Visualization 1: Stacked Area Chart  (REQUIRED)
# Kia/Hyundai vs Other over time
# Dataset: kiaHyundaiThefts.csv
# ============================================================

# NOTE: Assumes 'kia_thefts' is loaded and clean_names() was run.
# This block uses standard lubridate functions instead of custom helpers.

kia_time <- kia_thefts |>
  # Create a proper date column using year and month abbreviation
  mutate(
    month_num = match(month, month.abb),
    month_date = make_date(year, month_num, 1)
  ) |>
  filter(!is.na(month_date)) |>
  
  # Summarize totals by month
  group_by(month_date) |>
  summarise(
    kia_hyundai = sum(count_kia_hyundai_thefts, na.rm = TRUE),
    other       = sum(count_other_thefts, na.rm = TRUE),
    .groups = "drop"
  ) |>
  
  # Pivot for plotting
  pivot_longer(cols = c(kia_hyundai, other), 
               names_to = "type", 
               values_to = "thefts") |>
  
  # Recode for cleaner legend labels
  mutate(type = recode(type, 
                       kia_hyundai = "Kia/Hyundai", 
                       other = "All Other Vehicles"))

p1 <- ggplot(kia_time, aes(x = month_date, y = thefts, fill = type)) +
  geom_area(alpha = 0.9) +
  
  # Formatting axes
  scale_y_continuous(labels = comma) +
  scale_x_date(date_labels = "%b %Y", date_breaks = "6 months") + # Cleaner date axis
  
  # Manual Colors (Matches Viz 2 & Viz 6)
  scale_fill_manual(values = c(
    "Kia/Hyundai" = "#B22222",       # Firebrick Red
    "All Other Vehicles" = "#808080" # Grey
  )) +
  
  labs(
    title = "Kia/Hyundai Theft Surge Over Time",
    subtitle = "Monthly totals across included cities",
    x = NULL, # "Month" is obvious from the labels
    y = "Total Thefts",
    fill = ""
  ) +
  theme_minimal(base_size = 14) +
  theme(
    legend.position = "bottom",
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1) # Angled dates for readability
  )

ggsave(file.path(out_dir, "viz1_stacked_area_kia_vs_other.png"), p1, width = 11, height = 6, dpi = 300)

# ============================================================
# Visualization 2: Donut Chart  (REQUIRED)
# Share of Kia/Hyundai vs Other in Milwaukee dataset
# Dataset: KiaHyundaiMilwaukeeData.csv
# ============================================================

# Using snake_case names because clean_names() was run on load
milw_totals <- milwaukee |>
  summarise(
    kia_hyundai = sum(count_kia_hyundai_thefts, na.rm = TRUE),
    other       = sum(count_other_thefts, na.rm = TRUE)
  ) |>
  pivot_longer(everything(), names_to = "type", values_to = "thefts") |>
  mutate(
    # Recode for cleaner legend labels
    type = recode(type, 
                  kia_hyundai = "Kia/Hyundai", 
                  other = "All Other Vehicles"),
    # Calculate the weighted percentage
    pct  = thefts / sum(thefts)
  ) |>
  arrange(desc(type))

p2 <- ggplot(milw_totals, aes(x = 2, y = pct, fill = type)) +
  geom_col(width = 1, color = "white") +
  coord_polar(theta = "y") +
  xlim(0.5, 2.5) + 
  
  # Percent Labels
  geom_text(aes(label = percent(pct, accuracy = 0.1)),
            position = position_stack(vjust = 0.5),
            size = 5,       
            fontface = "bold", 
            color = "white") + 
  
  # Manual Colors
  scale_fill_manual(values = c(
    "Kia/Hyundai" = "#B22222",      
    "All Other Vehicles" = "#808080" 
  )) +
  
  labs(
    title = "Milwaukee Vehicle Thefts: Kia/Hyundai Share",
    subtitle = "Aggregated data (2019–2022)", 
    x = NULL, y = NULL, fill = ""
  ) +
  theme_void(base_size = 14) +
  theme(
    legend.position = "bottom",
    plot.title = element_text(hjust = 0.5, face = "bold"),
    plot.subtitle = element_text(hjust = 0.5)
  )

ggsave(file.path(out_dir, "viz2_donut_milwaukee_share.png"), p2, width = 9, height = 6, dpi = 300)

# ============================================================
# Visualization 3: Tree Map (REQUIRED)
# Cities most impacted by Kia/Hyundai thefts (VICE dataset)
# ============================================================

# 1. Read and Clean Data
# We use 'rename(date = 1)' to safely grab the first column 
# regardless of whether clean_names() calls it 'x', 'x1', or '...1'
vice_raw <- read_excel(xlsx_vice, sheet = "Data") |> 
  clean_names()

vice_kia <- vice_raw |>
  rename(date = 1) |>
  # Dynamic logic: Keep Date + any column that DOESN'T start with "x"
  # (In this specific Excel, "x" columns are the empty spacers or secondary metrics)
  select(date, any_of(names(vice_raw)[!str_detect(names(vice_raw), "^x")]))

# 2. Pivot and Aggregate
vice_totals <- vice_kia |>
  pivot_longer(
    cols = -date,
    names_to = "city",
    values_to = "kia_hyundai_thefts"
  ) |>
  mutate(
    # Force numbers (handles the "Kia/Hyundai" text row in the Excel header)
    kia_hyundai_thefts = readr::parse_number(as.character(kia_hyundai_thefts)),
    
    # Clean City Names (e.g., "el_paso" -> "El Paso")
    city = clean_city_label(city),
    city = recode(city,
                  "Cincinatti" = "Cincinnati",
                  "Mc Kinney, TX" = "McKinney, TX",
                  "Irving Texas" = "Irving, TX",
                  "Washington DC" = "Washington, DC")
    
  ) |>
  # Aggregate
  group_by(city) |>
  summarise(total_thefts = sum(kia_hyundai_thefts, na.rm = TRUE), .groups = "drop") |>
  filter(!is.na(total_thefts), total_thefts > 0) |>
  arrange(desc(total_thefts)) |>
  slice_head(n = 20) # Top 20 cities

# 3. Plot with Consistent Red Theme
p3 <- ggplot(vice_totals, aes(area = total_thefts, fill = total_thefts, label = city)) +
  geom_treemap(color = "white", size = 2) + # White borders define the boxes clearly
  
  # Text Labels
  geom_treemap_text(
    colour = "white",
    place = "centre",
    reflow = TRUE,  # Wraps text to fit the box
    grow = FALSE,   # "FALSE" often looks cleaner than "TRUE" for variable lengths
    min.size = 7
  ) +
  
  # Red Gradient (Matches your Kia Red theme)
  scale_fill_gradient(
    low = "#ffcccc",   # Pale Red (Low thefts)
    high = "#B22222",  # Firebrick Red (High thefts)
    labels = comma,
    name = "Total Thefts"
  ) +
  
  labs(
    title = "Cities Most Impacted by Kia/Hyundai Thefts",
    subtitle = "Aggregated counts (Top 20 Cities) from Vice News dataset",
    caption = "Source: Motherboard/Vice News"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = "right"
  )

ggsave(file.path(out_dir, "viz3_treemap_top_cities_vice.png"), p3, width = 11, height = 7, dpi = 300)

# ============================================================
# Visualization 4: Stacked Bar (REQUIRED)
# Theft composition by city
# Dataset: kiaHyundaiThefts.csv
# ============================================================

kia_by_city <- kia_thefts |>
  # 1. Aggregate Totals by City
  group_by(city, state) |>
  summarise(
    kia_hyundai = sum(count_kia_hyundai_thefts, na.rm = TRUE),
    other       = sum(count_other_thefts, na.rm = TRUE),
    .groups = "drop"
  ) |>
  
  # 2. Filter Top 12 Cities by Kia Volume
  arrange(desc(kia_hyundai)) |>
  slice_head(n = 12) |>
  mutate(city_state = paste0(city, ", ", state)) |>
  
  # 3. Pivot for Plotting
  pivot_longer(
    cols = c(kia_hyundai, other), 
    names_to = "type", 
    values_to = "thefts"
  ) |>
  mutate(type = recode(type, 
                       kia_hyundai = "Kia/Hyundai", 
                       other = "All Other Vehicles"))

p4 <- ggplot(kia_by_city, aes(x = reorder(city_state, -thefts, FUN = sum), y = thefts, fill = type)) +
  geom_col() +
  
  # Formatting
  scale_y_continuous(labels = comma) +
  
  # Consistent Colors
  scale_fill_manual(values = c(
    "Kia/Hyundai" = "#B22222",       # Firebrick Red
    "All Other Vehicles" = "#808080" # Grey
  )) +
  
  labs(
    title = "Vehicle Theft Composition by City",
    subtitle = "Top 12 cities (sorted by Kia/Hyundai volume)",
    x = NULL,
    y = "Total Thefts",
    fill = ""
  ) +
  theme_minimal(base_size = 14) +
  theme(
    legend.position = "bottom",
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1) # Angle text to prevent overlap
  )

ggsave(file.path(out_dir, "viz4_stacked_bar_city_composition.png"), p4, width = 12, height = 6, dpi = 300)

# ============================================================
# Visualization 5: Area Chart (REQUIRED)
# Overall auto theft trend 2019–2022
# Dataset: carTheftsMap.csv
# ============================================================

# 1. Clean & Prepare Data
# We select columns dynamically so we don't have to worry about exact names
map_years <- thefts_map |>
  # Ensure numeric conversion for all theft count columns
  mutate(
    across(starts_with("count"), ~ readr::parse_number(as.character(.x)))
  ) |>
  
  # Summarize totals by year (summing all columns that start with 'count')
  summarise(across(starts_with("count"), \(x) sum(x, na.rm = TRUE))) |>
  
  # Pivot to long format
  pivot_longer(
    cols = everything(),
    names_to = "year_col",
    values_to = "thefts"
  ) |>
  
  # Extract actual year integer from the column name (e.g., "count_car_thefts_2019" -> 2019)
  mutate(year = readr::parse_number(year_col)) |>
  arrange(year)

# 2. Plot
p5 <- ggplot(map_years, aes(x = year, y = thefts)) +
  geom_area(fill = "#404040", alpha = 0.8) + # Neutral Dark Grey for "Context"
  geom_line(color = "#404040", linewidth = 1) +
  geom_point(color = "#404040", size = 2) +
  
  scale_y_continuous(labels = comma) +
  scale_x_continuous(breaks = map_years$year) + # Force integer years on axis
  
  labs(
    title = "Context: Overall Auto Thefts (2019–2022)",
    subtitle = "Total thefts across all tracked agencies (Background Trend)",
    x = NULL,
    y = "Total Auto Thefts"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold"),
    panel.grid.minor.x = element_blank() # Remove minor gridlines for cleaner look
  )

ggsave(file.path(out_dir, "viz5_area_total_auto_thefts_2019_2022.png"), p5, width = 10, height = 6, dpi = 300)

# ============================================================
# Visualization 6: Line Chart
# The Milwaukee "Explosion": Trend over time
# Dataset: KiaHyundaiMilwaukeeData.csv
# ============================================================

# 1. Prepare Data: Convert to Date & Long Format
milw_trend <- milwaukee |>
  mutate(
    month_num = match(month, month.abb),
    date = make_date(year, month_num, 1)
  ) |>
  filter(!is.na(date)) |>
  select(date, count_kia_hyundai_thefts, count_other_thefts) |>
  pivot_longer(
    cols = -date, 
    names_to = "type", 
    values_to = "thefts"
  ) |>
  mutate(
    type = recode(type, 
                  count_kia_hyundai_thefts = "Kia/Hyundai", 
                  count_other_thefts = "All Other Vehicles")
  )

# 2. Plot: Line Chart comparing the two groups
p6 <- ggplot(milw_trend, aes(x = date, y = thefts, color = type)) +
  geom_line(linewidth = 1.2) +
  geom_point(size = 2) +
  
  # Consistent Colors (Red vs Grey)
  scale_color_manual(values = c(
    "Kia/Hyundai" = "#B22222",       # Firebrick Red (The Problem)
    "All Other Vehicles" = "#808080" # Grey (The Control Group)
  )) +
  
  scale_y_continuous(labels = comma) +
  scale_x_date(date_labels = "%b %Y", date_breaks = "6 months") +
  
  labs(
    title = "Milwaukee: The Kia/Hyundai 'Explosion'",
    subtitle = "Monthly theft counts: Kia/Hyundai vs. All Other Vehicles (2019–2022)",
    x = NULL,
    y = "Monthly Thefts",
    color = ""
  ) +
  theme_minimal(base_size = 14) +
  theme(
    legend.position = "bottom",
    plot.title = element_text(face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.minor = element_blank() # Cleaner background
  )

ggsave(file.path(out_dir, "viz6_line_milwaukee_trend.png"), p6, width = 10, height = 6, dpi = 300)

cat("\nDone. Charts saved to:\n")
print(out_dir)