drop table if exists deposition;
drop table if exists database_ref;
drop table if exists wf_class_dict;
drop table if exists wf_instance;
drop table if exists wf_task;
drop table if exists wf_reference;
drop table if exists da_users;
drop table if exists process_information;
drop table if exists site;
drop table if exists da_group;
drop table if exists sgcenters;
drop table if exists database_PDB_obs_spr;
drop table if exists database_related;
drop table if exists author_corrections;
drop table if exists dep_with_problems;
drop table if exists release_request;
drop table if exists contact_author;
drop table if exists status;
drop table if exists django_session;
drop table if exists manager_site;
drop view dep_last_instance;
drop view dep_instance;


-- Table deposition stores basic information about a structure 
create table deposition
(
 dep_set_id                 varchar(10)  not null,
 pdb_id                     varchar(4)   not null,
 initial_deposition_date    date                 ,
 annotator_initials         varchar(12)          ,
 deposit_site               varchar(8)           ,
 process_site               varchar(8)           ,
 status_code                varchar(5)           ,
 author_release_status_code varchar(5)           ,
 title                      varchar(400)         ,
 author_list                varchar(500)         ,
 exp_method                 varchar(50)          ,
 status_code_exp            varchar(4)           ,
 SG_center                  varchar(10)          ,
 PRIMARY KEY (dep_set_id)                      
 ) ENGINE=InnoDB;



-- wf_class_dict lists all work flow classes defined in the XML file
create table wf_class_dict
(
 wf_class_id          varchar(10)  not null,
 wf_class_name        varchar(20)  not null,
 title                varchar(50)          ,
 author               varchar(50)          ,
 version              varchar(8)           ,
 class_file           varchar(100)         ,
 PRIMARY KEY (wf_class_id)                         
) ENGINE=InnoDB;

-- wf_instance is for the instances created by WFE
create table wf_instance

(
 ordinal              int not null AUTO_INCREMENT PRIMARY KEY,
 wf_inst_id           varchar(10)  not null,
 wf_class_id          varchar(10)  not null,
 dep_set_id           varchar(10)  not null,
 owner                varchar(50)          ,
 inst_status          varchar(10)          ,
 status_timestamp     decimal(16,4)        ,
 KEY (wf_inst_id)                          ,
 KEY(wf_class_id)                          ,
 KEY(dep_set_id)     
) ENGINE=InnoDB;

-- wf_task is a child of wf_instance. It holds the progress of a WF task.
create table wf_task
(
 ordinal              int not null AUTO_INCREMENT PRIMARY KEY,
 wf_task_id           varchar(10)  not null,
 wf_inst_id           varchar(10)  not null,
 wf_class_id          varchar(10)  not null,
 dep_set_id           varchar(10)  not null,
 task_name            varchar(10)          ,
 task_status          varchar(10)  not null,
 status_timestamp     decimal(16,4)        ,
 task_type            varchar(25)          ,
 KEY (wf_task_id)                          ,
 KEY(wf_inst_id)                           ,
 KEY(wf_class_id)                          ,                     
 KEY(dep_set_id)
 ) ENGINE=InnoDB;


-- wf_reference holds all information between instances, tasks, and wfs that are not in above tables.
create table wf_reference
(
 dep_set_id           varchar(10)  not null,
 wf_inst_id           varchar(10)          ,
 wf_task_id           varchar(10)          ,
 wf_class_id          varchar(10)          ,
 hash_id              varchar(20)  not null,
 value                varchar(20)          ,
 KEY (dep_set_id)                          ,
 KEY(hash_id)                              ,
 KEY(wf_inst_id)                           ,
 KEY(wf_task_id)                           ,
 KEY(wf_class_id)                                                
) ENGINE=InnoDB;

-- following tables are designed based on the interface requirement from annotation team


-- da_users stores user information for logging in ;
 create table da_users
(
  user_name              varchar(20)  not null,
  password               varchar(10)  not null,
  da_group_id            int          not null,
  email                  varchar(30)  not null,
  initials               varchar(5)           ,
  first_name             varchar(50)          ,
  last_name              varchar(100)         ,
  PRIMARY KEY (user_name),
  KEY da_group_id (da_group_id)                     
) ENGINE=InnoDB;

INSERT INTO da_users VALUES ('ann','ann',2,'ann@a2nn.com','AN','Ann','Ann'),('BD','BD',5,'','BD','Batsal Devokta',''),('CS','CS',5,'','CS','Chenghua',' Shao'),('EP','EP',5,'','EP','Ezra','Peisach'),('GG','GG',5,'','GG','Guanghua',' Gao'),('GJS','GJS',3,'','GJS','Jawahar','Swaminathan'),('GS','GS',3,'','GS','Gaurav','Sahni'),('GVG','GVG',3,'','GVG','Glen','van Ginkel'),('IP','IP',5,'','IP','Irina','Persikova'),('JY','JY',5,'','JY','Jasmine','Young'),('JZ','JZ',5,'','JZ','Jing','Zhou'),('KM','KM',4,'','KM','Kanna','Matsuura'),('LD','LD',5,'','LD','Luigi','Dicostanzo'),('LT','LT',5,'','LT','Lihua','Tan'),('MC','MC',3,'','MC','Matthew','Conroy'),('MRS','MRS',5,'','MRS','Monica','Sekharhan'),('MZ','MZ',5,'','MZ','Marina','Zhuravleva'),('pdbe_ann','pdbe_ann',3,'','PeA','PDBe','Annotator'),('pdbe_ann2','pdbe_ann2',3,'','PeA2','PDBe2','Annotator'),('pdbe_ann3','pdbe_ann3',3,'','PeA3','PDBe3','Annotator'),('pdbjJPN','pdbjJPN',4,'','JPN','unassigned','unassiged'),('pdbj_ann','pdbj_ann',4,'','PjA','PDBj','Annotator'),('pdbj_ann2','pdbj_ann2',4,'','PjA3','Pj3','Annotator'),('rcsb_ann','rcsb_ann',5,'','RA','RCSB','Annotator'),('rcsb_ann2','rcsb_ann2',5,'','RA2','RCSB2','Annotator'),('RI','RI',4,'','RI','Reiko','Igarashi'),('SG','SG',5,'','SG','Sutapa','Ghosh'),('SS','SS',3,'','SS','Sanchayita','Sen'),('YK','YK',4,'','YM','Yumiko','Kengaku');

-- process_information is for tracking the process recordes of each structure 
 create table process_information
(
 dep_set_id               varchar(10)  not null,
 serial_number            int          not null,
 process_begin            datetime             ,
 process_end              datetime             ,
 remark                   varchar(50)          ,
 PRIMARY KEY (dep_set_id,serial_number)      
) ENGINE=InnoDB;

create table da_group 
(
  code             varchar(20) NOT NULL,
  group_name       varchar(20) NOT NULL,
  site             varchar(4)  NOT NULL,
  main_page        varchar(30)         ,
  da_group_id      int         NOT NULL,
  PRIMARY KEY (da_group_id)
) ENGINE=InnoDB;


INSERT INTO da_group VALUES ('ADMIN','Administrator','ALL','',1),('ANN','Annotator-test','ALL','Annotators.html',2),('ANN','PDBe - Annotators','PDBe','Annotators.html',3),('ANN','PDBJ - Annotators','PDBj','Annotators.html',4),('ANN','RCSB - Annotators','RCSB','Annotators.html',5);


create table site 
(
  code             varchar(4) NOT NULL DEFAULT '',
  verbose_name     varchar(150) DEFAULT NULL,
  PRIMARY KEY (code)
) ENGINE=InnoDB;



INSERT INTO site VALUES('RCSB', 'RCSB | Research Collaboratory for Structural Bioinformatics');
INSERT INTO site VALUES('PDBe', 'PDBe | Protein Data Bank Europe');
INSERT INTO site VALUES('PDBj', 'PDBj | Protein Data Bank Japan');
INSERT INTO site VALUES('BMRB', 'BMRM | Biological Magnetic Resonance Bank');
INSERT INTO site VALUES('ALL', 'All site for administration');



create table sgcenters 
(
  code             varchar(4) NOT NULL,
  verbose_name     varchar(250) NOT NULL,
  PRIMARY KEY (code)
) ENGINE=InnoDB;



INSERT INTO sgcenters VALUES('BSGI', ' Montreal-Kingston Bacterial Structural Genomics Initiative [BSGI]');
INSERT INTO sgcenters VALUES('CESG', ' Center for Eukaryotic Structural Genomics [CESG]');
INSERT INTO sgcenters VALUES('CHTS', 'Center for High-Throughput Structural Biology [CHTSB]');
INSERT INTO sgcenters VALUES('CSGI', 'Center for Structural Genomics of Infectious Diseases [CSGID]');
INSERT INTO sgcenters VALUES('CSMP', 'Center for Structures of Membrane Proteins [CSMP]');
INSERT INTO sgcenters VALUES('ISFI', 'Integrated Center for Structure and Function Innovation [ISFI]');
INSERT INTO sgcenters VALUES('JCSG', 'Joint Center for Structural Genomics [JCSG]');
INSERT INTO sgcenters VALUES('MCSG', 'Midwest Center for Structural Genomics [MCSG]');
INSERT INTO sgcenters VALUES('NESG', 'Northeast Structural Genomics Consortium [NESG]');
INSERT INTO sgcenters VALUES('NYCO', 'New York Consortium on Membrane Protein Structure [NYCOMPS]');
INSERT INTO sgcenters VALUES('NYSG', 'New York SGX Research Center for Structural Genomics [NYSGXRC]');
INSERT INTO sgcenters VALUES('OCSP', 'Ontario Centre for Structural Proteomics [OCSP]');
INSERT INTO sgcenters VALUES('RIKE', 'RIKEN Structural Genomics/Proteomics Initiative [RIKEN]');
INSERT INTO sgcenters VALUES('S2F', 'Structure 2 Function Project [S2F]');
INSERT INTO sgcenters VALUES('SSGC', 'Seattle Structural Genomics Center for Infectious Disease [SSGCID]');
INSERT INTO sgcenters VALUES('BIGS', 'Bacterial targets at IGS-CNRS [BIGS]');
INSERT INTO sgcenters VALUES('BSGC', 'Berkeley Structural Genomics Center [BSGC]');
INSERT INTO sgcenters VALUES('ISPC', 'Israel Structural Proteomics Center [ISPC]');
INSERT INTO sgcenters VALUES('MSGP', 'Marseilles Structural Genomics Program @ AFMB [MSGP]');
INSERT INTO sgcenters VALUES('OPPF', ' Oxford Protein Production Facility [OPPF]');
INSERT INTO sgcenters VALUES('SECS', 'Southeast Collaboratory for Structural Genomics [SECSG]');
INSERT INTO sgcenters VALUES('SGC', 'Structural Genomics Consortium [SGC]');
INSERT INTO sgcenters VALUES('SGPP', 'Structural Genomics of Pathogenic Protozoa Consortium [SGPP]');
INSERT INTO sgcenters VALUES('SGX', 'SGX Pharmaceuticals [SGX]');
INSERT INTO sgcenters VALUES('SPIN', 'Structural Proteomics in Europe [SPINE]');
INSERT INTO sgcenters VALUES('TBSG', 'TB Structural Genomics Consortium [TBSGC]');
INSERT INTO sgcenters VALUES('XMTB', 'Mycobacterium Tuberculosis Structural Proteomics Project [XMTB]');
INSERT INTO sgcenters VALUES('YSG', 'Paris-Sud Yeast Structural Genomics [YSG]');

-- Holding entries that are obsolete or superseded
create table  database_PDB_obs_spr 
( 
  dep_set_id               varchar(10)    not null,
  id                       varchar(10)            ,
  date                     datetime               ,
  pdb_id                   varchar(10)            ,
  replace_pdb_id           varchar(10)    not null,
  PRIMARY KEY (dep_set_id,replace_pdb_id)
) ENGINE=InnoDB;

-- Holding other database related infomation
create table  database_related
( 
  dep_set_id               varchar(10)    not null,
  db_name                  varchar(10)    not null,
  details                  varchar(200)           ,
  content_type             varchar(10)            ,
  db_id                    varchar(10)    not null,
  PRIMARY KEY (dep_set_id,db_name,db_id)
) ENGINE=InnoDB;

-- databese_ref may hold all related database IDs.
create table database_ref
(
  dep_set_id               varchar(10)  not null,
  database_name            varchar(20)  not null,
  database_code            varchar(10)  not null,
  PRIMARY KEY (dep_set_id,database_name)
) ENGINE=InnoDB;


-- author_correction is for tracking author's correction sent after deposition.
 create table author_corrections
(
 ordinal              int not null AUTO_INCREMENT PRIMARY KEY,
 dep_set_id               varchar(10)  not null,
 content                  varchar(40)  not null,
 sending_date             date                 ,
 remark                   varchar(50)          ,
 KEY (dep_set_id)      
) ENGINE=InnoDB;

-- author_correction is for tracking author's correction sent after deposition.
 create table dep_with_problems
(
 ordinal              int not null AUTO_INCREMENT PRIMARY KEY,
 dep_set_id               varchar(10)  not null,
 type                     varchar(10)  not null,
 detail                   varchar(50)          ,
 KEY (dep_set_id)      
) ENGINE=InnoDB;

-- release_request is for holding the entries that author wants to release.
 create table release_request
(
 dep_set_id               varchar(10)  not null,
 citation                 varchar(100)         ,
 release_date             date                 ,
 PubMed_id                int(11)              ,
 KEY (dep_set_id)      
) ENGINE=InnoDB;

-- contact_author is for storing depositor's contact information.
 create table contact_author
(
 dep_set_id               varchar(10)    not null,
 name_salutation          varchar(15)        null,
 name_first               varchar(40)    not null,
 name_last                varchar(65)    not null,
 name_mi                  varchar(50)        null,
 role                     varchar(50)    not null,
 email                    varchar(255)   not null,
 address_1                varchar(520)   not null,
 address_2                varchar(255)       null,
 address_3                varchar(255)       null,
 city                     varchar(60)    not null,
 state_province           varchar(70)        null,
 postal_code              varchar(128)   not null,
 country                  varchar(50)    not null,
 phone                    varchar(60)        null,
 fax                      varchar(60)        null,
 organization_type        varchar(40)    not null,
 PRIMARY KEY (dep_set_id,name_first,name_last)
) ENGINE=InnoDB;


CREATE TABLE status (
  code varchar(4) NOT NULL,
  verbose_name varchar(100) DEFAULT NULL,
  PRIMARY KEY (code)
) ENGINE=InnoDB;

INSERT INTO status VALUES('WAIT', 'WAIT [Awaiting Processing]');
INSERT INTO status VALUES('PROC', 'PROC [Under processing]');
INSERT INTO status VALUES('AUTH', 'AUTH [Waiting for Author]');
INSERT INTO status VALUES('REPL', 'REPL [Replacement Coordinates]');
INSERT INTO status VALUES('REL', 'REL [Released]');
INSERT INTO status VALUES('HPUB', 'HPUB [Released upon pubblication]');
INSERT INTO status VALUES('HOLD', 'HOLD [Hold for one year]');
INSERT INTO status VALUES('OBS', 'OBS [Obsolete]');
INSERT INTO status VALUES('WDRN', 'WDRN [Withdrawn]');


CREATE TABLE django_session (
  session_key       varchar(40)  NOT NULL,
  session_data      longtext     NOT NULL,
  expire_date       datetime     NOT NULL,
  PRIMARY KEY (session_key)
) ENGINE=InnoDB ;


CREATE TABLE manager_site (
  id           int(11) NOT  NULL AUTO_INCREMENT,
  code         varchar(4)   NOT NULL,
  display_name varchar(100) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

-- the user needs "Create View" privilege

CREATE VIEW dep_instance 
as select 
d.dep_set_id AS dep_set_id,
d.pdb_id AS pdb_id,
d.initial_deposition_date AS dep_initial_deposition_date,
d.annotator_initials AS annotator_initials,
d.deposit_site AS dep_deposit_site,
d.process_site AS dep_process_site,
d.status_code AS dep_status_code,
d.author_release_status_code AS dep_author_release_status_code,
d.title AS dep_title,
d.author_list AS dep_author_list,
d.exp_method AS dep_exp_method,
d.status_code_exp AS dep_status_code_exp,
d.SG_center AS dep_SG_center,
wfi.ordinal AS inst_ordinal,
wfi.wf_inst_id AS inst_id,
wfi.owner AS inst_owner,
wfi.inst_status AS inst_status,
wfi.status_timestamp AS inst_status_timestamp,
wfi.wf_class_id AS class_id,
wfcd.wf_class_name AS class_name,
wfcd.title AS class_title,
wfcd.author AS class_author,
wfcd.version AS class_version,
wfcd.class_file AS class_file 
from ((deposition d join wf_instance wfi) join wf_class_dict wfcd) 
where ((d.dep_set_id = wfi.dep_set_id) and 
(wfi.wf_class_id = wfcd.wf_class_id));

CREATE VIEW dep_last_instance
AS select
   distinct d1.dep_set_id AS dep_set_id,
   d1.pdb_id AS pdb_id,
   d1.dep_initial_deposition_date AS dep_initial_deposition_date,
   d1.annotator_initials AS annotator_initials,
   d1.dep_deposit_site AS dep_deposit_site,
   d1.dep_process_site AS dep_process_site,
   d1.dep_status_code AS dep_status_code,
   d1.dep_author_release_status_code AS dep_author_release_status_code,
   d1.dep_title AS dep_title,
   d1.dep_author_list AS dep_author_list,
   d1.dep_exp_method AS dep_exp_method,
   d1.dep_status_code_exp AS dep_status_code_exp,
   d1.dep_SG_center AS dep_SG_center,
   d1.inst_ordinal AS inst_ordinal,
   d1.inst_id AS inst_id,
   d1.inst_owner AS inst_owner,
   d1.inst_status AS inst_status,
   d1.inst_status_timestamp AS inst_status_timestamp,
   d1.class_id AS class_id,
   d1.class_name AS class_name,
   d1.class_title AS class_title,
   d1.class_author AS class_author,
   d1.class_version AS class_version,
   d1.class_file AS class_file
from dep_instance d1 join dep_instance d2
where d1.dep_set_id = d2.dep_set_id and 
d1.inst_status_timestamp = (select max(d2.inst_status_timestamp) 
from dep_instance d2 where d2.dep_set_id = d1.dep_set_id);
