source('official_timss_reproduction_gate.R')
suppressPackageStartupMessages(library(foreign))
dir.create('timss_principal_output',showWarnings=FALSE)
out <- 'timss_principal_output'

survey_est <- function(d,prefix,calc,weight='TOTWGT') {
  cols<-paste0(prefix,sprintf('%02d',1:5))
  stopifnot(all(cols %in% names(d)),all(c(weight,'JKZONE','JKREP') %in% names(d)))
  d<-d[is.finite(d[[weight]]) & d[[weight]]>0 & !is.na(d$JKZONE) & !is.na(d$JKREP) &
       rowSums(!is.finite(as.matrix(d[,cols])))==0,]
  full<-sapply(1:5,function(p)calc(d,d[[cols[p]]],d[[weight]]))
  if(is.null(dim(full)))full<-matrix(full,nrow=1)
  jk<-matrix(0,nrow(full),nrow(full),dimnames=list(rownames(full),rownames(full)))
  for(p in 1:5) for(z in unique(d$JKZONE)) {
    w<-d[[weight]]; i<-d$JKZONE==z
    w[i]<-w[i]*ifelse(d$JKREP[i]==1,2,0)
    delta<-calc(d,d[[cols[p]]],w)-full[,p]
    jk<-jk+tcrossprod(delta)/5
  }
  v<-jk+1.2*cov(t(full))
  est<-rowMeans(full); se<-sqrt(pmax(0,diag(v)))
  data.frame(term=names(est),estimate=unname(est),se=unname(se),
             lower=unname(est-1.96*se),upper=unname(est+1.96*se),
             p=unname(2*pnorm(-abs(est/se))),n=nrow(d),row.names=NULL)
}

group_calc <- function(groupvar) function(d,y,w) {
  g<-d[[groupvar]]
  pr<-sapply(1:3,function(k)sum(w[g==k])/sum(w))
  means<-sapply(1:3,function(k)weighted.mean(y[g==k],w[g==k]))
  x<-c(pr,means,means[1]-means[3],means[2]-means[3],means[1]-means[2])
  names(x)<-c(paste0('share_',1:3),paste0('mean_',1:3),'very_minus_medium','high_minus_medium','very_minus_high')
  x
}
reg_calc <- function(teacher=FALSE) function(d,y,w) {
  X<-cbind(intercept=1,very_high=as.numeric(d$ACDGEAS==1),
           high=as.numeric(d$ACDGEAS==2),girl=as.numeric(d$ASBG01==1),
           resource_some=as.numeric(d$ASDGHRL==2),
           resource_few=as.numeric(d$ASDGHRL==3))
  if(teacher) X<-cbind(X,teacher_emphasis=d$ATBGEAS-10)
  b<-as.vector(solve(crossprod(X,w*X),crossprod(X,w*y)))
  names(b)<-colnames(X); b
}
load_timss <- function(yr) {
  base<-if(yr==2019)'TIMSS2019/T19_G4_SPSS Data/' else 'SPSS Data/'
  suf<-if(yr==2019)'m7.sav' else 'm8.sav'
  rd<-function(prefix)read.spss(paste0(base,prefix,'twn',suf),to.data.frame=TRUE,use.value.labels=FALSE)
  s<-rd('asg'); h<-rd('ash'); c<-rd('acg'); t<-rd('atg'); l<-rd('ast')
  stopifnot(!anyDuplicated(s$IDSTUD),!anyDuplicated(c$IDSCHOOL),!anyDuplicated(h$IDSTUD))
  s$home_joined<-s$IDSTUD %in% h$IDSTUD
  sh<-merge(s,c[,c('IDCNTRY','IDSCHOOL','ACBGEAS','ACDGEAS')],by=c('IDCNTRY','IDSCHOOL'),all.x=TRUE,sort=FALSE)
  stopifnot(nrow(sh)==nrow(s))
  lm<-l[l$IDSUBJ %in% c(1,3),]
  teacher_key<-paste(t$IDCNTRY,t$IDSCHOOL,t$IDTEALIN)
  stopifnot(!anyDuplicated(teacher_key))
  tm<-merge(lm,t[,c('IDCNTRY','IDSCHOOL','IDTEALIN','ATBGEAS','ATDGEAS')],
            by=c('IDCNTRY','IDSCHOOL','IDTEALIN'),all.x=TRUE,sort=FALSE)
  tm<-merge(tm,s[,c('IDCNTRY','IDSTUD','ASBG01','ASDGHRL')],by=c('IDCNTRY','IDSTUD'),all.x=TRUE,sort=FALSE)
  tm<-merge(tm,c[,c('IDCNTRY','IDSCHOOL','ACDGEAS')],by=c('IDCNTRY','IDSCHOOL'),all.x=TRUE,sort=FALSE)
  stopifnot(nrow(tm)==nrow(lm))
  list(student=sh,teacher=tm,school=c,home=h,link=lm)
}

meta<-data.frame()
main_models<-data.frame()
teacher_models<-data.frame()
groups<-data.frame()
for(yr in c(2019,2023)) {
  data<-load_timss(yr)
  s<-data$student; t<-data$teacher; c<-data$school
  ps<-s$ACDGEAS %in% 1:3
  main<-s[ps,]
  adj<-main[main$ASBG01 %in% 1:2 & main$ASDGHRL %in% 1:3,]
  linked<-t[t$ACDGEAS %in% 1:3 & t$ASBG01 %in% 1:2 & t$ASDGHRL %in% 1:3 &
              is.finite(t$ATBGEAS) & t$ATBGEAS<100 & is.finite(t$MATWGT) & t$MATWGT>0,]
  z<-survey_est(main,'ASMMAT',group_calc('ACDGEAS'));z$year<-yr;groups<-rbind(groups,z)
  z<-survey_est(adj,'ASMMAT',reg_calc(FALSE));z$year<-yr;main_models<-rbind(main_models,z)
  z<-survey_est(linked,'ASMMAT',reg_calc(TRUE),'MATWGT');z$year<-yr;teacher_models<-rbind(teacher_models,z)
  meta<-rbind(meta,data.frame(year=yr,students=nrow(s),schools=nrow(c),
    school_valid=sum(c$ACDGEAS %in% 1:3),school_very=sum(c$ACDGEAS==1,na.rm=TRUE),
    school_high=sum(c$ACDGEAS==2,na.rm=TRUE),school_medium=sum(c$ACDGEAS==3,na.rm=TRUE),
    home_matched=sum(s$home_joined),student_school_valid=nrow(main),
    student_model_n=nrow(adj),math_links=nrow(data$link),
    teacher_model_rows=nrow(linked),teacher_model_students=length(unique(linked$IDSTUD)),
    principal_missing_students=sum(!ps)))
}

write.csv(meta,file.path(out,'sample_flow.csv'),row.names=FALSE)
write.csv(groups,file.path(out,'principal_group_means.csv'),row.names=FALSE)
write.csv(main_models,file.path(out,'principal_adjusted_models.csv'),row.names=FALSE)
write.csv(teacher_models,file.path(out,'principal_teacher_models.csv'),row.names=FALSE)

# Content and cognitive domain changes for the research context.
domains<-read.csv('timss_2019_2023_math_domain_changes.csv')
write.csv(domains,file.path(out,'timss_domain_changes.csv'),row.names=FALSE)

print(meta,row.names=FALSE)
cat('\nPRINCIPAL GROUP MEANS\n');print(groups[,c('year','term','estimate','se','lower','upper')],row.names=FALSE)
cat('\nADJUSTED MODELS\n');print(main_models[,c('year','term','estimate','se','lower','upper','p')],row.names=FALSE)
cat('\nTEACHER MODELS\n');print(teacher_models[,c('year','term','estimate','se','lower','upper','p')],row.names=FALSE)

