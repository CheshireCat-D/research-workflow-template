#!/usr/bin/env Rscript
# Independent base-R reconstruction. Does not source or run the reviewed code.
# Usage: Rscript evals/public-data/independent_check.R INPUT.csv NEW-OUTPUT
args <- commandArgs(trailingOnly=TRUE)
if (length(args) != 2L) {
  stop("Usage: Rscript evals/public-data/independent_check.R INPUT.csv NEW-OUTPUT", call.=FALSE)
}
input <- args[[1L]]
out <- args[[2L]]
if (!file.exists(input) || dir.exists(input)) {
  stop("INPUT must be an existing CSV file", call.=FALSE)
}
if (file.exists(out) || dir.exists(out)) {
  stop("OUTPUT must be a new directory; refusing to overwrite", call.=FALSE)
}
if (!dir.exists(dirname(out))) {
  stop("OUTPUT parent directory must already exist", call.=FALSE)
}
if (!dir.create(out, recursive=FALSE, showWarnings=FALSE)) {
  stop("Cannot create a new OUTPUT directory", call.=FALSE)
}
d <- read.csv(input, na.strings=c("", "NA"), stringsAsFactors=FALSE, check.names=FALSE)
required <- c("species", "island", "body_mass_g", "sex", "year")
stopifnot(all(required %in% names(d)))
stopifnot(is.numeric(d$body_mass_g), is.numeric(d$year))
species <- sort(unique(d$species[!is.na(d$species)]))
islands <- sort(unique(d$island[!is.na(d$island)]))
years <- sort(unique(d$year[!is.na(d$year)]))
known_sex <- !is.na(d$sex) & d$sex %in% c("female", "male")
mass_known <- !is.na(d$body_mass_g) & is.finite(d$body_mass_g)
overall <- !is.na(d$species) & known_sex & mass_known
stratified <- overall & !is.na(d$island) & !is.na(d$year)
write.csv(data.frame(field=names(d), missing=colSums(is.na(d)), denominator=nrow(d)),
          file.path(out,"missing_by_field.csv"), row.names=FALSE)
missing_patterns <- as.data.frame(table(sex_missing=is.na(d$sex), mass_missing=!mass_known), stringsAsFactors=FALSE)
write.csv(missing_patterns, file.path(out,"missing_overlap.csv"), row.names=FALSE)
write.csv(as.data.frame(table(species=d$species,sex=d$sex,useNA="ifany")),
          file.path(out,"raw_species_sex_counts.csv"),row.names=FALSE)
audit <- data.frame(data_row=seq_len(nrow(d)), csv_line=seq_len(nrow(d))+1L,
                    d[c("species","island","year","sex","body_mass_g")],
                    included_overall=overall,included_stratified=stratified,
                    sex_missing=is.na(d$sex),mass_missing=!mass_known)
write.csv(audit,file.path(out,"independent_row_audit.csv"),row.names=FALSE,na="")
stats <- function(z) c(n=length(z),mean=if(length(z)) mean(z) else NA_real_,
                       sd=if(length(z)>=2L) sd(z) else NA_real_,
                       median=if(length(z)) median(z) else NA_real_,
                       min=if(length(z))min(z)else NA_real_,max=if(length(z))max(z)else NA_real_)
grouped <- do.call(rbind,lapply(species,function(s) do.call(rbind,lapply(c("female","male"),function(x) {
 z <- d$body_mass_g[overall & d$species==s & !is.na(d$species) & d$sex==x]
 ix<-!is.na(d$species) & d$species==s & !is.na(d$sex) & d$sex==x
 data.frame(species=s,sex=x,raw_n=sum(ix),mass_missing_n=sum(ix & !mass_known),t(stats(z)),row.names=NULL)
}))))
write.csv(grouped,file.path(out,"grouped_by_species_sex.csv"),row.names=FALSE)
grid <- expand.grid(species=species,island=islands,year=years,stringsAsFactors=FALSE)
grid <- grid[order(grid$species,grid$island,grid$year),]
strata <- do.call(rbind,lapply(seq_len(nrow(grid)),function(i){
 g<-grid[i,]; ix<-stratified & d$species==g$species & d$island==g$island & d$year==g$year
 ix[is.na(ix)]<-FALSE
 f<-d$body_mass_g[ix & d$sex=="female"];m<-d$body_mass_g[ix & d$sex=="male"]
 allix <- !is.na(d$species) & !is.na(d$island) & !is.na(d$year) & d$species==g$species & d$island==g$island & d$year==g$year
 allix[is.na(allix)]<-FALSE
 data.frame(g,raw_n=sum(allix),excluded_n=sum(allix & !overall),female_n=length(f),male_n=length(m),
            female_mean=if(length(f))mean(f) else NA_real_, male_mean=if(length(m))mean(m)else NA_real_,
            female_sd=if(length(f)>=2L)sd(f) else NA_real_,male_sd=if(length(m)>=2L)sd(m)else NA_real_,
            female_median=if(length(f))median(f)else NA_real_,male_median=if(length(m))median(m)else NA_real_,
            difference=if(length(f)&&length(m))mean(m)-mean(f)else NA_real_,
            difference_pct=if(length(f)&&length(m))100*(mean(m)-mean(f))/mean(f)else NA_real_,
            median_difference=if(length(f)&&length(m))median(m)-median(f)else NA_real_,row.names=NULL)
}))
write.csv(strata,file.path(out,"strata.csv"),row.names=FALSE,na="")
contrasts <- do.call(rbind,lapply(species,function(s){
 f<-d$body_mass_g[overall & d$species==s & !is.na(d$species) & d$sex=="female"]
 m<-d$body_mass_g[overall & d$species==s & !is.na(d$species) & d$sex=="male"]
 st<-strata[strata$species==s & !is.na(strata$difference),]
 w<-(st$female_n+st$male_n)/sum(st$female_n+st$male_n)
 u<-d$body_mass_g[!is.na(d$species) & d$species==s & !known_sex & mass_known]
 # Exhaustive assignment: bit 0=female, bit 1=male, retaining every known-sex mass.
 sensitivity <- numeric()
 if(length(u)<=16L) {
  for(k in 0:(2^length(u)-1L)) {
   b <- if(length(u)) as.logical(intToBits(as.integer(k))[seq_along(u)]) else logical()
   sensitivity <- c(sensitivity,mean(c(m,u[b]))-mean(c(f,u[!b])))
  }
 }
 ix<-!is.na(d$species) & d$species==s
 data.frame(species=s,raw_n=sum(ix),excluded_n=sum(ix & !overall),
            missing_sex_n=sum(ix & is.na(d$sex)),missing_mass_n=sum(ix & !mass_known),
            female_n=length(f),male_n=length(m),female_mean=mean(f),male_mean=mean(m),
            difference=mean(m)-mean(f),difference_pct=100*(mean(m)-mean(f))/mean(f),
            median_difference=median(m)-median(f),
            comparable_strata=nrow(st),positive_strata=sum(st$difference>0),
            stratum_min=min(st$difference),stratum_max=max(st$difference),
            stratum_range=max(st$difference)-min(st$difference),
            common_weight_female_mean=sum(w*st$female_mean),common_weight_male_mean=sum(w*st$male_mean),
            common_weight_difference=sum(w*st$difference),standardization_rows_n=sum(st$female_n+st$male_n),
            unknown_sex_known_mass_n=length(u),
            assignments=length(sensitivity),sensitivity_min=if(length(sensitivity))min(sensitivity)else NA_real_,
            sensitivity_max=if(length(sensitivity))max(sensitivity)else NA_real_)
}))
write.csv(contrasts,file.path(out,"species_contrasts.csv"),row.names=FALSE)
overview <- data.frame(metric=c("raw_n","overall_included_n","overall_excluded_n","stratified_included_n",
                                "complete_all_columns_n","sex_missing_n","mass_missing_n","sex_and_mass_missing_n",
                                "sex_missing_mass_known_n","mass_missing_sex_known_n","grid_strata_n",
                                "raw_observed_strata_n","comparable_strata_n","no_observation_strata_n",
                                "zero_or_one_sex_strata_n","year_min","year_max"),
                       value=c(nrow(d),sum(overall),sum(!overall),sum(stratified),sum(complete.cases(d)),
                               sum(is.na(d$sex)),sum(!mass_known),sum(is.na(d$sex)&!mass_known),
                               sum(is.na(d$sex)&mass_known),sum(known_sex&!mass_known),nrow(strata),
                               sum(strata$raw_n>0),sum(!is.na(strata$difference)),sum(strata$raw_n==0),
                               sum(strata$raw_n>0&is.na(strata$difference)),min(years),max(years)))
write.csv(overview,file.path(out,"overview.csv"),row.names=FALSE)
capture.output(sessionInfo(),file=file.path(out,"R-sessionInfo.txt"))
print(overview,row.names=FALSE)
print(grouped,row.names=FALSE)
print(contrasts,row.names=FALSE)
