"""
   File:    WfSchemaMap.py
   A data class containing schema definitions for WF Database.

   __author__    = "Li Chen"
   __email__     = "lchen@rcsb.rutgers.edu"
   __version__   = "V0.01"
   __Date__      = "April 21, 2010"
   
"""

class WfSchemaMap:
    _schemaMap = { 
        "DEPOSITION" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"              : "dep_set_id",
                        "PDB_ID"                  : "pdb_id",
                        "INITIAL_DEPOSITION_DATE" : "initial_deposition_date",
                        "ANNOTATOR_INITIALS"      : "annotator_initials",
                        "DEPOSIT_SITE"            : "deposit_site",
                        "PROCESS_SITE"            : "process_site",
                        "STATUS_CODE"             : "status_code",
                        "AUTHOR_RELEASE_STATUS_CODE" : "author_release_status_code",
                        "TITLE"                   : "title",
                        "AUTHOR_LIST"             : "author_list",
                        "EXP_METHOD"              : "exp_method",
                        "STATUS_CODE_EXP"         : "status_code_exp",
                        "SG_CENTER"               : "sg_center",
                        "TITLE_EMDB"              : "title_emdb",
                        "AUTHOR_LIST_EMDB"        : "author_list_emdb",
                        "DEP_AUTHOR_RELEASE_STATUS_CODE_EMDB" : "dep_author_release_status_code_emdb",
                        "STATUS_CODE_EMDB"        : "status_code_emdb",
                        "DATE_BEGIN_PROCESSING"   : "date_begin_processing",
                        "DATE_END_PROCESSING"     : "date_end_processing",
                        "DEPPW"                   : "depPW",
                        "NOTIFY"                  : "notify",
                        "EMAIL"                   : "email",
                        "LOCKING"                 : "locking",
                        "COUNTRY"                 : "country",
                        "NMOLECULE"               : "nmolecule",
                        "EMDB_ID"                 : "emdb_id",
                        "BMRB_ID"                 : "bmrb_id",
                        "STATUS_CODE_BMRB"        : "status_code_bmrb",
                        "STATUS_CODE_OTHER"       : "status_code_other",
                        "POST_REL_STATUS"         : "post_rel_status",
                        "POST_REL_RECVD_COORD"    : "post_rel_recvd_coord",
                        "POST_REL_RECVD_COORD_DATE" : "post_rel_recvd_coord_date"},
                "TABLE_NAME"  : "deposition"},
        "DATABASE_REF" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"              : "dep_set_id",
                        "DATABASE_NAME"           : "database_name",
                        "DATABASE_CODE"           : "database_code"},
                "TABLE_NAME"  : "database_ref"},
        "WF_TASK" : {
                "ATTRIBUTES" :  {
                        "ORDINAL"             : "ordinal",
                        "WF_TASK_ID"          : "wf_task_id",
                        "WF_INST_ID"          : "wf_inst_id",
                        "WF_CLASS_ID"         : "wf_class_id",
                        "DEP_SET_ID"          : "dep_set_id",
                        "TASK_NAME"           : "task_name",
                        "TASK_STATUS"         : "task_status",
                        "STATUS_TIMESTAMP"    : "status_timestamp",
                        "TASK_TYPE"           : "task_type"},
                "TABLE_NAME"  : "wf_task"},
        "WF_INSTANCE" : {
                "ATTRIBUTES" :  {
                        "ORDINAL"             : "ordinal",
                        "WF_INST_ID"          : "wf_inst_id",
                        "WF_CLASS_ID"         : "wf_class_id",
                        "DEP_SET_ID"          : "dep_set_id",
                        "OWNER"               : "owner",
                        "INST_STATUS"         : "inst_status",
                        "STATUS_TIMESTAMP"    : "status_timestamp"},
                "TABLE_NAME"  : "wf_instance"},
        "WF_REFERENCE" : {
                "ATTRIBUTES" :  {
                        "DEP_SET_ID"          : "dep_set_id",
                        "WF_INST_ID"          : "wf_inst_id",
                        "WF_TASK_ID"          : "wf_task_id",
                        "WF_CLASS_ID"         : "wf_class_id",
                        "HASH_ID"             : "hash_id",
                        "VALUE"               : "value"},
                "TABLE_NAME"  : "wf_reference"},
        "WF_CLASS_DICT" : {
                "ATTRIBUTES" :  {
                        "WF_CLASS_ID"         : "wf_class_id",
                        "WF_CLASS_NAME"       : "wf_class_name",
                        "WF_CLASS_FILE"       : "class_file",
                        "TITLE"               : "title",
                        "AUTHOR"              : "author",
                        "VERSION"             : "version"},
                "TABLE_NAME"  : "wf_class_dict"},
        "PROCESS_INFORMATION" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"        : "dep_set_id",
                        "SERIAL_NUMBER"     : "serial_number",
                        "PROCESS_BEGIN"     : "process_begin",
                        "PROCESS_END"       : "process_end",
                        "REMARK"            : "remark"},
                "TABLE_NAME"  : "process_information"},
        "DA_USERS" : {
                "ATTRIBUTES"  : {
                        "USER_NAME"        : "user_name",
                        "PASSWORD"         : "password",
                        "GROUPNAME"        : "groupname",
                        "EMAIL"            : "email",
                        "INITIALS"         : "initials"},
                "TABLE_NAME"  : "da_users"},
        "DATABASE_RELATED" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"        : "dep_set_id",
                        "DB_NAME"           : "db_name",
                        "DETAILS"           : "details",
                        "CONTENT_TYPE"      : "content_type",
                        "DB_ID"             : "db_id"},
                "TABLE_NAME"  : "database_related"},
        "DATABASE_PDB_OBS_SPR" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"       : "dep_set_id",
                        "ID"               : "id",
                        "DATE"             : "date",
                        "PDB_ID"           : "pdb_id",
                        "REPLACE_PDB_ID"   : "replace_pdb_id"},
                "TABLE_NAME"  : "database_PDB_obs_spr"},
        "AUTHOR_CORRECTIONS" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"        : "dep_set_id",
                        "CORRECTIONS"       : "corrections",
                        "SENDING_DATE"      : "sending_date",
                        "REMARK"            : "content_type"},
                "TABLE_NAME"  : "author_corrections"},
        "DEP_WITH_PROBLEMS" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"        : "dep_set_id",
                        "PROBLEM_TYPE"      : "problem_type",
                        "PROBLEM_DETAILS"   : "problem_details"},
                "TABLE_NAME"  : "dep_with_problems"},
        "RELEASE_REQUEST" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"      : "dep_set_id",
                        "REQ_CITATION"        : "req_citation",
                        "RELEASE_DATE"    : "release_date",
                        "PUBMED_ID"       : "PubMed_id"},
                "TABLE_NAME"  : "release_request"},
        "CONTACT_AUTHOR" : {
                "ATTRIBUTES"  : {
                        "DEP_SET_ID"        : "dep_set_id",
                        "CITATION"          : "name_salutation",
                        "NAME_FIRST"        : "name_first",
                        "NAME_LAST"         : "name_last",
                        "NAME_MI"           : "name_mi",
                        "ROLE"              : "role",
                        "EMAIL"             : "email",
                        "ADDRESS_1"         : "address_1",
                        "ADDRESS_2"         : "address_2",
                        "ADDRESS_3"         : "address_3",
                        "CITY"              : "city",
                        "STATE_PROVINCE"    : "state_province",
                        "POSTAL_CODE"       : "postal_code",
                        "COUNTRY"           : "country",
                        "PHONE"             : "phone",
                        "FAX"               : "fax",
                        "ORGANIZATION_TYPE" : "organization_type"},
                "TABLE_NAME"  : "release_request"},
        "SITE" : {
                "ATTRIBUTES"  : {
                        "CODE"           : "code",
                        "VERBOSE_NAME"   : "verbose_name"},
                "TABLE_NAME"  : "site"},
        "DA_GROUP" : {
                "ATTRIBUTES"  : {
                        "CODE"           : "code",
                        "GROUPNAME"      : "groupname",
                        "SITE"           : "site",
                        "MAIN_PAGE"      : "main_page"},
                "TABLE_NAME"  : "da_group"},
        "SGCENTERS" : {
                "ATTRIBUTES"  : {
                        "CODE"           : "code",
                        "VERBOSE_NAME"   : "verbose_name"},
                "TABLE_NAME"  : "sgcenters"},
                
        "COMMUNICATION" : {
                "ATTRIBUTES"  : {
                        "ORDINAL"           : "ordinal",
                        "SENDER"            : "sender",
                        "RECEIVER"          : "receiver",
                        "DEP_SET_ID"        : "dep_set_id", 
                        "WF_CLASS_ID"       : "wf_class_id",
                        "WF_INST_ID"        : "wf_inst_id",
                        "WF_CLASS_FILE"     : "wf_class_file",
                        "COMMAND"           : "command",
                        "STATUS"            : "status",
                        "STATUS_TIMESTAMP"  : "status_timestamp", 
                        "PARENT_DEP_SET_ID" : "parent_dep_set_id", 
                        "PARENT_WF_CLASS_ID": "parent_wf_class_id",
                        "PARENT_WF_INST_ID" : "parent_wf_inst_id",
                                            
                        },
                "TABLE_NAME"  : "communication"},
        "ENGINE_MONITORING" : {
                "ATTRIBUTES"  : {
                        "CPU_ID"                : "cpu_id",
                        "TOTAL_MEM"             : "total_mem",
                        "TOTAL_PHYSICAL_MEM"    : "total_physical_mem",
                        "TOTAL_VIRTUAL_MEM"     : "total_virtual_mem", 
                        "TOTAL_MEM_USAGE"       : "total_mem_usage",
                        "PHYSICAL_MEM_USAGE"    : "physical_mem_usage",
                        "VIRTUAL_MEM_USAGE"     : "virtual_mem_usage",
                        "CPU_PROCESSES"         : "cpu_processes",
                        "IDS_SET"               : "ids_set",                      
                        },
                "TABLE_NAME"  : "engine_monitoring"},                
       
        }

    # following lists are used in the WfDbApi
    
    _columnForStatus = ['STATUS_CODE','INST_STATUS','TASK_STATUS']
    _objectTables = ['DEPOSITION','WF_CLASS_DICT','WF_INSTANCE','WF_TASK','WF_REFERENCE','DA_USERS']
    _tables = ['DEPOSITION',
               'WF_CLASS_DICT',
               'WF_INSTANCE',
               'WF_TASK',
               'WF_REFERENCE',
               'DA_USERS',
               'DATABASE_PDB_OBS_SPR',
               'DATABASE_REF',
               'DATABASE_RELATED',
               'AUTHOR_CORRECTIONS',
               'RELEASE_REQUEST',
               'DEP_WITH_PROBLEMS',
               'CONTACT_AUTHOR',
               'PROCESS_INFORMATION',
               'SITE',
               'DA_GROUP',
               'SGCENTERS', 
               'COMMUNICATION', 
               'ENGINE_MONITORING',
               ]
    _usefulItems = ['STATUS_CODE',
                    'INST_STATUS',
                    'TASK_STATUS',
                    'DATABASE_CODE',
                    'REPLACE_PDB_ID',
                    'ID',
                    'CONTENT_TYPE',
                    'DB_ID',
                    'DB_NAME',
                    'RELATIONSHIP',
                    'ASSOCIATED_IDS',
                    'ASSESSION_CODE',
                    'CORRECTIONS',
                    'REQ_CITATION',
                    'PROBLEM_TYPE',
                    'PROBLEM_DETAILS',
                    'PUBMED_ID'
                    ]
    _objIds = ['DEP_SET_ID',
               'WF_CLASS_ID',
               'WF_INST_ID',
               'WF_TASK_ID']
    _referencePairs = ['HASH_ID','VALUE']
    _userInfo = ['USER_NAME',
                 'PASSWORD',
                 'GROUPNAME',
                 'EMAIL',
                 'INITIALS'
                 ]
    
   
    _selectColumns = {2: ['deposition.dep_set_id',
                          'deposition.pdb_id',
                          'deposition.status_code',
                          'deposition.author_release_status_code',
                          'deposition.exp_method',
                          'deposition.annotator_initials',
                          'wf_class_dict.wf_class_id',
                          'wf_class_dict.wf_class_name',
                          'wf_class_dict.version',
                          'wf_instance.wf_inst_id',
                          'wf_instance.owner',
                          'wf_instance.inst_status',
                          'wf_instance.status_timestamp',
                          'wf_task.wf_task_id',
                          'wf_task.task_name',
                          'wf_task.task_status',
                          'wf_task.status_timestamp'
                          ],
                      1: ['DEP_SET_ID',
                          'EXP_METHOD',
                          'PDB_ID',
                          'STATUS_CODE',
                          'AUTHOR_RELEASE_STATUS_CODE',
                          'INITIAL_DEPOSITION_DATE',
                          'STATUS_CODE_EXP',
                          'ANNOTATOR_INITIALS',
                          'AUTHOR_LIST',
                          'SG_CENTER'
                          ]
                     }
    _constraintList={'DEP_SET_ID'          : 'deposition.dep_set_id',
                     'WF_CLASS_ID'         : 'wf_class_dict.wf_class_id',
                     'WF_INST_ID'          : 'wf_instance.wf_inst_id',
                     'WF_TASK_ID'          : 'wf_task.wf_task_id',
                     'STATUS_CODE'         : 'deposition.status_code',
                     'PDB_ID'              : 'deposition.pdb_id',
                     'DEPOSIT_SITE'        : 'deposition.deposit_site',
                     'PROCESS_SITE'        : 'deposition.process_site',
                     'ANNOTATOR_INITIALS'  : 'deposition.annotator_initials',
                     'EXP_METHOD'          : 'deposition.exp_method',
                     'SG_CENTER'           : 'deposition.sg_center',
                     'INST_STATUS'         : 'wf_instance.inst_status',
                     'INST_STATUS_TIMESTP' : 'wf_instance.status_timestamp',
                     'TASK_STATUS_TIMESTP' : 'wf_task.status_timestamp',
                     'TASK_STATUS'         : 'wf_task.task_status',
                     'OWNER'               : 'wf_instance.owner'
                    }
    
    # crossing search from wf_instance,wf_class_dict,deposition and wf_task
    
    _tableJoinSyntext = " FROM wf_instance left join wf_class_dict on " \
                  +"wf_instance.wf_class_id= wf_class_dict.wf_class_id " \
                  +"left join deposition on (wf_instance.wf_class_id=" \
                  +"wf_class_dict.wf_class_id and wf_instance.dep_set_id" \
                  +"=deposition.dep_set_id) left join wf_task on " \
                  +"(wf_task.wf_inst_id=wf_instance.wf_inst_id and " \
                  +"wf_task.dep_set_id=deposition.dep_set_id)"
    
    _orderBy = {1: "order by dep_set_id",
                2: " order by deposition.dep_set_id, wf_instance.wf_inst_id desc," \
                   +"wf_instance.ordinal desc,wf_task.ordinal desc",
                3: ['author_release_status_code','initial_deposition_date']
                }


   
                       
    def __init__(self):
        pass

