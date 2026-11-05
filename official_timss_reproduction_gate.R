suppressPackageStartupMessages(library(foreign))
get_spss <- function(p) read.spss(p,to.data.frame=TRUE,use.value.labels=FALSE)
paths <- list(
  t19='TIMSS2019/T19_G4_SPSS Data/asgtwnm7.sav',
  t23='SPSS Data/asgtwnm8.sav'
)
load_rdata <- function(p) {e<-new.env(); e[[load(p,envir=e)[1]]]}
pv_est <- function(d,prefix,condition=rep(TRUE,nrow(d))) {
  cols<-paste0(prefix,sprintf('%02d',1:5))
  d<-d[condition & is.finite(d$TOTWGT) & d$TOTWGT>0 &
       !is.na(d$JKZONE) & !is.na(d$JKREP) &
       rowSums(!is.finite(as.matrix(d[,cols])))==0,]
  calc<-function(w,p) weighted.mean(d[[cols[p]]],w)
  theta<-sapply(1:5,function(p)calc(d$TOTWGT,p))
  jk<-0
  for(p in 1:5) for(z in unique(d$JKZONE)) {
    w<-d$TOTWGT; idx<-d$JKZONE==z
    w[idx]<-w[idx]*ifelse(d$JKREP[idx]==1,2,0)
    jk<-jk+(calc(w,p)-theta[p])^2/5
  }
  se<-sqrt(jk+1.2*var(theta))
  c(n=nrow(d),mean=mean(theta),se=se)
}
t19<-get_spss(paths$t19)
t23<-get_spss(paths$t23)
targets<-data.frame(
 dataset=c(rep('t19',4),rep('t23',4)),
 scale=c('ASMMAT','ASMNUM','ASMGEO','ASMDAT','ASMMAT','ASMNUM','ASMGEO','ASMDAT'),
 official_mean=c(599,599,607,590,607,602,622,601),
 official_se=c(1.9,1.7,1.8,2.4,1.7,1.6,1.8,2.0)
)
res<-do.call(rbind,lapply(seq_len(nrow(targets)),function(i){
  r<-targets[i,]; x<-pv_est(get(as.character(r$dataset)),as.character(r$scale))
  data.frame(dataset=r$dataset,scale=r$scale,n=x['n'],mean=x['mean'],se=x['se'],
             official_mean=r$official_mean,official_se=r$official_se)
}))
res$mean_round<-round(res$mean)
res$se_round<-round(res$se,1)
res$pass<-res$mean_round==res$official_mean & res$se_round==res$official_se
print(res,row.names=FALSE)
write.csv(res,'official_timss_reproduction_gate.csv',row.names=FALSE)
if(!all(res$pass)) stop('Official reproduction gate failed; do not proceed to substantive analysis.')
