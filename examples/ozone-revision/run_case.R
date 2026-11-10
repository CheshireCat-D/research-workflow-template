# Usage: Rscript --vanilla run_case.R OUTPUT_DIRECTORY
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Supply one output directory.")
out <- args[[1L]]
options(digits = 16, OutDec = ".")

estimate <- function(days) {
  days$hot <- days$Temp >= 85
  by_month <- lapply(split(days, days$Month), function(d) {
    hot <- d$Ozone[d$hot]
    other <- d$Ozone[!d$hot]
    difference <- if (any(!is.na(hot)) && any(!is.na(other))) {
      mean(hot, na.rm = TRUE) - mean(other, na.rm = TRUE)
    } else NA_real_
    data.frame(month = d$Month[1], hot_eligible = length(hot), hot_measured = sum(!is.na(hot)),
               other_eligible = length(other), other_measured = sum(!is.na(other)), difference = difference)
  })
  monthly <- do.call(rbind, by_month)
  common <- monthly$month[!is.na(monthly$difference)]
  observed <- subset(days, !is.na(Ozone))
  supported <- subset(observed, Month %in% common)
  pooled <- function(d) mean(d$Ozone[d$hot]) - mean(d$Ozone[!d$hot])
  june <- monthly[monthly$month == 6, ]
  scope <- c("Jun-Sep; four months equally weighted", "Jun-Sep; observed days pooled",
             "May-Sep; observed days pooled")
  table <- data.frame(
    estimate_id = c("equal_month", "supported_pooled", "all_pooled"),
    value = c(mean(monthly$difference, na.rm = TRUE), pooled(supported), pooled(observed)),
    unit = "ppb", scope = paste("Hot >= 85 F vs cooler;", scope),
    hot_measured = c(sum(supported$hot), sum(supported$hot), sum(observed$hot)),
    other_measured = c(sum(!supported$hot), sum(!supported$hot), sum(!observed$hot)),
    june_hot_measured = june$hot_measured, june_hot_eligible = june$hot_eligible,
    june_other_measured = june$other_measured, june_other_eligible = june$other_eligible,
    artifact = "brief.md, figure.svg, caption.txt")
  list(table = table, monthly = monthly)
}

make_outputs <- function(days, folder, title) {
  result <- estimate(days)
  tab <- result$table
  dir.create(folder, recursive = TRUE, showWarnings = FALSE)
  put <- function(lines, name) writeLines(lines, file.path(folder, name), useBytes = TRUE)
  write.csv(tab, file.path(folder, "estimates.csv"), row.names = FALSE)
  write.csv(result$monthly, file.path(folder, "monthly.csv"), row.names = FALSE, na = "")
  rows <- c("Equal months (primary)", "Pooled Jun-Sep", "Pooled May-Sep")
  numbers <- sprintf("%+.2f %s", tab$value, tab$unit)
  values <- paste0(rows, ": ", numbers)
  june <- sprintf("June coverage: %d/%d hot and %d/%d other days.",
                  tab$june_hot_measured[1], tab$june_hot_eligible[1],
                  tab$june_other_measured[1], tab$june_other_eligible[1])
  caption <- c(title, "Ozone difference (hot minus cooler), parts per billion.",
               "Hot: maximum temperature at LaGuardia Airport >= 85 F.",
               "Ozone: 13:00-15:00 at Roosevelt Island.", june,
               "May had no hot days. Each supported month has 1/4 weight in the primary estimate.")
  put(caption, "caption.txt")
  body <- c(paste0("# ", title), "", values, "", caption[-1], "",
            "These differences describe observed afternoons. Coverage and the two measurement sites limit interpretation.")
  put(body, "brief.md")

  # The SVG preserves editable text. The PDF uses the same estimates, labels and caption.
  axis_max <- ceiling(max(tab$value) / 10) * 10
  x <- function(v) 305 + v / axis_max * 465
  y <- c(104, 155, 206)
  ticks <- seq(0, axis_max, by = 10)
  put(c('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 830 350" role="img" aria-labelledby="title desc">',
        sprintf('<title id="title">%s</title>', title),
        '<desc id="desc">Three descriptive differences in observed mean ozone, in ppb.</desc>',
        '<rect width="830" height="350" fill="white"/>',
        '<g font-family="sans-serif" fill="#16344c">',
        sprintf('<text x="22" y="37" font-size="22">%s</text>', title),
        '<text x="22" y="65" font-size="15">Difference in measured afternoon ozone (hot minus cooler), ppb</text>',
        sprintf('<line x1="%.1f" x2="%.1f" y1="84" y2="226" stroke="#d4dfe3"/>', x(ticks), x(ticks)),
        sprintf('<line x1="305" x2="%.1f" y1="%d" y2="%d" stroke="#7f959c"/>', x(tab$value), y, y),
        sprintf('<circle cx="%.1f" cy="%d" r="7" fill="#08725f"/>', x(tab$value), y),
        sprintf('<text x="22" y="%d" font-size="16">%s: %s</text>', y + 5, rows, numbers),
        sprintf('<text x="%.1f" y="247" text-anchor="middle" font-size="13">%d</text>', x(ticks), ticks),
        sprintf('<text x="22" y="285" font-size="15">%s</text>', june),
        '<text x="22" y="313" font-size="14">LaGuardia maximum temperature at least 85 F; Roosevelt Island ozone, 13:00-15:00.</text>',
        '</g></svg>'), "figure.svg")

  grDevices::pdf(file.path(folder, "brief.pdf"), width = 8.3, height = 5.3, useDingbats = FALSE)
  on.exit(grDevices::dev.off())
  graphics::par(mar = c(4.7, 9, 2.9, 1.1), mgp = c(1.7, 0.5, 0), tcl = -0.2)
  graphics::plot(tab$value, 3:1, xlim = c(0, axis_max), ylim = c(0.7, 3.4), axes = FALSE,
                 xlab = "Difference in measured afternoon ozone (hot minus cooler, ppb)", ylab = "", type = "n",
                 col = "#08725f", main = title)
  graphics::abline(v = ticks, col = "#d4dfe3")
  graphics::segments(0, 3:1, tab$value, 3:1, col = "#7f959c")
  graphics::points(tab$value, 3:1, pch = 19, col = "#08725f")
  graphics::axis(1, at = ticks)
  graphics::axis(2, at = 3:1, labels = rows, las = 1, tick = FALSE, cex.axis = 0.83)
  graphics::text(tab$value, 3:1 + 0.18, numbers, cex = 0.84)
  graphics::mtext(june, side = 1, line = 2.7, cex = 0.8)
  graphics::mtext("LaGuardia maximum >= 85 F; Roosevelt Island ozone, 13:00-15:00; May has no hot days.",
                  side = 1, line = 3.65, cex = 0.73)

  put(c('{"table":"estimates.csv","id_column":"estimate_id","checks":[',
        '{"row":"equal_month","file":"brief.md","after":"Equal months (primary):","expect":"{value:+.2f} {unit}"},',
        sprintf('{"row":"%s","file":"figure.svg","after":"%s:","expect":"{value:+.2f} {unit}"},',
                tab$estimate_id, rows),
        paste0('{"row":"equal_month","file":"caption.txt","after":"June coverage:",',
               '"expect":"{june_hot_measured}/{june_hot_eligible} hot and {june_other_measured}/{june_other_eligible} other days."}]}')),
      "checks.json")
}

observed <- datasets::airquality
stopifnot(nrow(observed) == 153, all(!is.na(observed$Temp)))
make_outputs(observed, file.path(out, "observed"), "New York ozone, 1973: observed data")
edited <- observed
first_may <- which(edited$Month == 5 & edited$Day == 1)
stopifnot(length(first_may) == 1, edited$Ozone[first_may] == 41)
edited$Ozone[first_may] <- 42
make_outputs(edited, file.path(out, "simulation"), "Simulated May 1 edit: New York ozone, 1973")
