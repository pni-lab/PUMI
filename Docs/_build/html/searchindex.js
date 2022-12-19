Search.setIndex({docnames:["PUMI","PUMI.interfaces","PUMI.pipelines","PUMI.pipelines.anat","PUMI.pipelines.dwi","PUMI.pipelines.func","PUMI.pipelines.func.info","PUMI.pipelines.multimodal","PUMI.plot","definitions","examples","index","modules","pipelines","tests"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":4,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.viewcode":1,sphinx:56},filenames:["PUMI.rst","PUMI.interfaces.rst","PUMI.pipelines.rst","PUMI.pipelines.anat.rst","PUMI.pipelines.dwi.rst","PUMI.pipelines.func.rst","PUMI.pipelines.func.info.rst","PUMI.pipelines.multimodal.rst","PUMI.plot.rst","definitions.rst","examples.rst","index.rst","modules.rst","pipelines.rst","tests.rst"],objects:{"":[[9,0,0,"-","definitions"]],"PUMI.engine":[[0,1,1,"","AnatPipeline"],[0,1,1,"","BidsPipeline"],[0,1,1,"","FuncPipeline"],[0,1,1,"","GroupPipeline"],[0,1,1,"","NestedMapNode"],[0,1,1,"","NestedNode"],[0,1,1,"","NestedWorkflow"],[0,1,1,"","PumiPipeline"],[0,1,1,"","QcPipeline"]],"PUMI.engine.NestedMapNode":[[0,2,1,"","output_dir"]],"PUMI.engine.NestedNode":[[0,2,1,"","output_dir"]],"PUMI.engine.NestedWorkflow":[[0,2,1,"","connect"]],"PUMI.interfaces":[[1,0,0,"-","HDBet"]],"PUMI.interfaces.HDBet":[[1,1,1,"","HDBet"],[1,1,1,"","HDBetInputSpec"],[1,1,1,"","HDBetOutputSpec"]],"PUMI.interfaces.HDBet.HDBet":[[1,3,1,"","input_spec"],[1,3,1,"","output_spec"]],"PUMI.pipelines.anat":[[3,0,0,"-","anat2mni"],[3,0,0,"-","anat_proc"],[3,0,0,"-","func_to_anat"],[3,0,0,"-","segmentation"]],"PUMI.pipelines.anat.anat2mni":[[3,4,1,"","anat2mni_ants"],[3,4,1,"","anat2mni_ants_hardcoded"],[3,4,1,"","anat2mni_fsl"],[3,4,1,"","qc"]],"PUMI.pipelines.anat.anat_proc":[[3,4,1,"","anat_proc"]],"PUMI.pipelines.anat.func_to_anat":[[3,4,1,"","bbr"]],"PUMI.pipelines.anat.segmentation":[[3,4,1,"","bet_fsl"],[3,4,1,"","bet_hd"],[3,4,1,"","defacing"],[3,4,1,"","pydeface_wrapper"],[3,4,1,"","qc_segmentation"],[3,4,1,"","qc_tissue_segmentation"],[3,4,1,"","tissue_segmentation_fsl"]],"PUMI.pipelines.func":[[5,0,0,"-","compcor"],[5,0,0,"-","concat"],[5,0,0,"-","data_censorer"],[5,0,0,"-","deconfound"],[5,0,0,"-","func_proc"],[5,0,0,"-","temporal_filtering"]],"PUMI.pipelines.func.compcor":[[5,4,1,"","anat_noise_roi"],[5,4,1,"","compcor"],[5,4,1,"","compcor_qc"]],"PUMI.pipelines.func.concat":[[5,4,1,"","concat"]],"PUMI.pipelines.func.data_censorer":[[5,4,1,"","datacens_workflow_threshold"],[5,4,1,"","qc_datacens"]],"PUMI.pipelines.func.deconfound":[[5,4,1,"","despiking_afni"],[5,4,1,"","motion_correction_mcflirt"],[5,4,1,"","nuisance_removal"],[5,4,1,"","qc"],[5,4,1,"","qc_motion_correction_mcflirt"],[5,4,1,"","qc_nuisance_removal"]],"PUMI.pipelines.func.func_proc":[[5,4,1,"","func_proc_despike_afni"]],"PUMI.pipelines.func.temporal_filtering":[[5,4,1,"","qc_temporal_filtering"],[5,4,1,"","temporal_filtering"]],"PUMI.pipelines.multimodal":[[7,0,0,"-","image_manipulation"]],"PUMI.pipelines.multimodal.image_manipulation":[[7,4,1,"","get_info"],[7,4,1,"","pick_volume"],[7,4,1,"","timecourse2png"],[7,4,1,"","vol2png"]],"PUMI.plot":[[8,0,0,"-","carpet_plot"]],"PUMI.plot.carpet_plot":[[8,4,1,"","plot_carpet"]],"PUMI.utils":[[0,4,1,"","TsExtractor"],[0,4,1,"","above_threshold"],[0,4,1,"","calc_friston_twenty_four"],[0,4,1,"","calculate_FD_Jenkinson"],[0,4,1,"","concatenate"],[0,4,1,"","create_coregistration_qc"],[0,4,1,"","create_segmentation_qc"],[0,4,1,"","drop_first_line"],[0,4,1,"","get_config"],[0,4,1,"","get_indx"],[0,4,1,"","get_ref_from_templateflow"],[0,4,1,"","get_ref_locally"],[0,4,1,"","get_reference"],[0,4,1,"","max_from_txt"],[0,4,1,"","mean_from_txt"],[0,4,1,"","mist_labels"],[0,4,1,"","mist_modules"],[0,4,1,"","plot_carpet_ts"],[0,4,1,"","plot_roi"],[0,4,1,"","registration_ants_hardcoded"],[0,4,1,"","relabel_atlas"],[0,4,1,"","rpn_model"],[0,4,1,"","scale_vol"],[0,4,1,"","scrub_image"]],"examples.test":[[10,4,1,"","hh"]],"pipelines.rpn_signature":[[13,4,1,"","calculate_connectivity"],[13,4,1,"","collect_predictions"],[13,4,1,"","predict_pain_sensitivity"]],"tests.test_afni":[[14,1,1,"","TestDespike"]],"tests.test_afni.TestDespike":[[14,2,1,"","test_despike"]],"tests.test_ants":[[14,1,1,"","TestAnts"]],"tests.test_ants.TestAnts":[[14,2,1,"","test_ants"]],"tests.test_fsl":[[14,1,1,"","TestFsl"]],"tests.test_fsl.TestFsl":[[14,2,1,"","test_fsl"]],PUMI:[[0,0,0,"-","engine"],[0,0,0,"-","utils"]],examples:[[10,0,0,"-","bet_bids_func_subworkflow"],[10,0,0,"-","bet_bids_subworkflow"],[10,0,0,"-","defacing_ex_bids"],[10,0,0,"-","despiking_bids_ex"],[10,0,0,"-","ex_bids_pipeline"],[10,0,0,"-","ex_compcor"],[10,0,0,"-","ex_func_proc"],[10,0,0,"-","ex_func_to_anat_bids"],[10,0,0,"-","ex_motion_correction"],[10,0,0,"-","ex_tmpfilt"],[10,0,0,"-","get_rpn_model"],[10,0,0,"-","rpn_preproc"],[10,0,0,"-","test"]],pipelines:[[13,0,0,"-","rpn_signature"]],tests:[[14,0,0,"-","test_afni"],[14,0,0,"-","test_ants"],[14,0,0,"-","test_fsl"]]},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","method","Python method"],"3":["py","attribute","Python attribute"],"4":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:attribute","4":"py:function"},terms:{"0":[0,5,8],"00":[],"000189":[],"000196":[],"000207":[],"000254":[],"000276":[],"000297":[],"000308":[],"000333":[],"000365":[],"000373":[],"000383":[],"000387":[],"000391":[],"000401":[],"000425":[],"000429":[],"000434":[],"000435":[],"000436":[],"000465":[],"000466":[],"000494":[],"000514":[],"000525":[],"000527":[],"000544":[],"00058":[],"000602":[],"000609":[],"000617":[],"00064":[],"000646":[],"000703":[],"000719":[],"00076":[],"000804":[],"000864":[],"000894":[],"000906":[],"000946":[],"000968":[],"001":[],"001033":[],"001212":[],"001248":[],"001295":[],"001318":[],"001559":[],"001577":[],"00165":[],"001676":[],"001909":[],"001_t1w":[],"001_t1w_reorient":[],"001_t1w_reoriented_brain":[],"001_t1w_reoriented_brain_flirt":[],"001_t1w_reoriented_brain_flirt_inv":[],"001_t1w_reoriented_brain_mask":[],"001_t1w_reoriented_brain_plot":[],"001_task":[],"002002":[],"002046":[],"002135":[],"00245":[],"002546":[],"002764":[],"002812":[],"003054":[],"003412":[],"00344":[],"003602":[],"003743":[],"003878":[],"004737":[],"005":[],"005324":[],"00563":[],"006059":[],"00622":[],"008":5,"00m":[],"01":[],"010616":[],"015318":[],"017":5,"018":5,"022217":[],"025363":[],"028":[],"02_t1w":0,"03":5,"033":[],"036431":[],"046532":[],"072":[],"08":5,"0m":[],"0x0":[],"0x1":[],"0x2":[],"0x7f6dad90ad00":[],"1":[0,5,8],"10":5,"100":0,"1000":[],"100013":[],"1000x500x250":[],"100x50x30":[],"101":[],"1016":5,"102":[],"104":[],"105":[],"107":[],"108":[],"109":[],"11":[],"110":[],"111":[],"112":[],"113":[],"114":[],"115":[],"116":[],"117":[],"118":[],"119":[],"12":[],"120":[],"121":[],"122":0,"123":[],"124":[],"125":[],"125624":[],"126":[],"127":[],"128":[],"129":[],"13":[],"130":[],"131":[],"132":[],"133":[],"13397":[],"134":[],"135":[],"136":[],"137":[],"138":[],"139":[],"14":[],"140":[],"141":[],"142":[],"143":[],"144":[],"145":[],"146":[],"147":[],"148":[],"149":[],"15":[],"150":[0,8],"151":[],"152":[],"153":[],"154":[0,8],"156":[],"157":[],"158":[0,8],"159":[],"16":[],"160":[],"161":[],"1620":[],"164":[],"165":[],"166":[],"167":[],"168":[],"169":[],"17":5,"170":[],"170064":[],"171":[],"172":[],"173":[],"174":[],"1748365":[],"175":[],"176":[],"176763":[],"177":[],"178":[],"179":[],"18":[],"180":[],"181":[],"181307":[],"182":[],"183":[],"185":[],"186":[],"187":[],"19":[],"190":[],"191":[],"192":[],"193":[],"194":[],"1948":[],"195":[],"196":[],"197":[],"197775":[],"198":[],"199":[],"1d":0,"1e":[],"2":[0,5],"20":[],"200":[],"2002":5,"2007":5,"2008":[],"201":[],"2011":5,"2012":5,"2017":[0,8],"2018":[3,5],"202":[],"2021":[],"2022":[],"203":[],"204":[],"205":[],"206":[],"207":[],"208":[],"209":[],"21":[],"210":[],"211":[],"212":[],"213":[],"214":[],"2142":5,"215":[],"2154":5,"216":[],"218307":[],"22":[],"221":[],"222":[],"222m":[],"223":[],"224":[],"225":[],"226":[],"227":[],"228":[],"228895":[],"229":[],"23":[],"230":[],"231":[],"232":[],"233":[],"234":[],"235":[],"236":[],"237":[],"237471":[],"238":[],"239":[],"24":0,"240":[],"241":[],"242":[],"243":[],"244":[],"245":[],"246":[],"247":[],"248":[],"249":[],"25":[],"250":[],"251":[],"252":[],"253":[],"254":[],"255":[],"255723":[],"256":[],"256color":[],"257":[],"258":[],"259":[],"26":[],"260":[],"261":[],"262":[],"263":[],"264":[],"265":[],"266":[],"267":[],"268":[],"2684250000000001":[],"269":[],"27":[],"270":[],"271":[],"272":[],"272895":[],"273":[],"274":[],"275":[],"276":[],"278":[],"279":[],"28":[],"280":[],"281":[],"282":[],"283":[],"284":[],"285":[],"286":[],"287":[],"288":[],"29":[],"290":[],"29003770":[],"2e32":[],"2mm":0,"3":[0,5],"30":[],"302":[],"31":[],"316573":[],"32":[],"32ff5b8bfb55":[],"32m":[],"33":[],"335768":[],"339873":[],"34":[],"34m":[],"35":[],"350737":[],"356666":[],"36":[],"36906":[],"37":[],"379":[],"38":[],"380":[],"39":[],"3d":[3,5,7,8],"3dbandpass":5,"3dcalc":0,"3ddespik":[],"3dresampl":[],"3dwarp":[],"3f":[],"3x2x1":[],"4":0,"40":[],"41":[],"415078":[],"419262":[],"42":[],"421989":[],"43":[],"44":[],"446b":[],"45":[],"4540":[],"457":[],"45cf":[],"46":[],"463411":[],"47":[],"48":[],"49":[],"490376":[],"4d":[0,3,5,7,8],"4dfile":0,"4x2x1":[],"5":[0,5],"50":[],"51":[],"5199999809265137":[],"52":[],"53":[],"53886":[],"54":[],"544916":[],"55":[],"56":[],"560791":[],"57":[],"58":[],"580329":[],"586":[],"59":5,"599324":[],"5x0":[],"6":[],"60":[],"61":[],"617745":[],"62":[],"63":[],"64":[],"64678":[],"65":[],"66":[],"660661":[],"67":[],"68":[],"69":[],"6df":5,"7":0,"70":[],"71":[],"719926":[],"72":[],"73":[],"74":[],"75":[],"75354":[],"76":[],"764853":[],"77":[],"777948":[],"78":[],"79":[],"790498a1bdc44073850ce4bdbdc2b842":[],"7m":[],"7z":[],"8":[],"80":[],"81":[],"818362":[],"825":5,"8252":[],"83":[],"839":[],"84":[],"841":5,"8439778":[],"85":[],"855487":[],"86":[],"861185":[],"87":[],"88":[],"89":[],"9":[],"90":[],"91":[],"92":[],"922657a8":[],"94":[],"95":[],"96":[],"97":[],"98":0,"98541":[],"98bced4a":[],"99":[],"993134":[],"995":[],"9b60365733bd":[],"case":[0,3,7,8,14],"class":[0,1,14],"default":[0,5,8],"do":5,"export":[],"final":[],"float":8,"function":[0,3,5,7,8],"import":[],"int":0,"new":0,"return":[0,5,7,8],"true":[0,3,7,8],"try":0,"var":[],"void":[],"while":[],A:[0,5],Be:0,For:[0,1,3],If:[0,8,13],In:[0,3,7,8],NO:[],NOT:0,No:[],One:3,The:[0,3,5,7,8],These:0,_:[],_output:[],_plot:[],_subject_001:[],_subject_:[],_tran:[],a0:[],a260:[],aac:[],abbrevi:0,abin:[],abl:0,about:[0,1],above_threshold:0,absolut:[0,5,8],ac:3,accor_d:[],accord:5,accur:5,acknowledg:[0,3,5],acompcor:5,acquisit:[],across:[0,8],adapt:[0,3,5,7,8],add:[],add_contour:[],affin:[],afni:5,afni_21:[],afni_nifti_type_warn:[],after:[3,5,8],agent:[],ains_ad:[],ains_pd:[],ains_v:[],al:5,algorithm:[],alia:1,all:[5,7,8],along:[0,8],alpha:0,alreadi:[3,5],also:[0,3,8],alz:[],amd64:[],ami:[],an:[0,5,8],anat2mni:[0,2],anat2mni_:3,anat2mni_ants_hardcod:3,anat2mni_fsl:3,anat2mni_warpfield:3,anat:[0,2,12],anat_csf_segment:3,anat_gm_segment:3,anat_noise_roi:5,anat_proc:[0,2],anat_wm_segment:3,anatom:[3,5],anatomical_preprocessing_wf:[],anatpipelin:0,angle_rep:[],annot:0,anoth:0,ant:3,ants_hardcod:[],antsapplytransform:[],antsinstallexampl:[],antspath:[],antsregistr:[],api:3,append:[],appli:[],applic:[],apply_isoxfm:[],apply_mask:[],apply_xfm:[],ar:[0,5],arbitrari:7,arc:[],arg:0,argument:[],argwher:[],aris:5,arj:[],arrai:0,artifact:5,asf:[],astyp:[],atk:[],atla:0,atlas_fil:0,attent:3,au:[],author:[],auto:0,automask:[],automat:[0,8],avail:0,avi:[],await:5,awar:0,ax:[0,5,8],axi:[0,8],b:5,background:[0,3],background_fil:0,baf1:[],balint:[3,5],bamf_desktop_file_hint:[],bandpass:5,bannist:5,barn:5,base:[0,1,5,14],base_dir:0,base_directori:[],bash:[],bbr:[3,5],bbreg_arg:[],bbreg_target:[],bbrslope:[],bbrtype:[],bd:[],beawar:7,becaus:0,been:0,befor:5,behzadi:5,being:8,believ:[],bet:[1,3],bet_bids_func_subworkflow:12,bet_bids_subworkflow:12,bet_fsl:3,bet_hd:3,bet_tool:3,bet_vol:[],bet_wf:[],between:8,bewar:0,bg_img:0,bgvalu:[],bias_field:[],bias_it:[],bias_lowpass:[],bid:0,bidspipelin:0,big:[],bin:[],binari:8,bit:[],black:0,black_bg:0,blob:[3,5],bmp:[],bodi:5,bold:[],bool:[0,3,8],bottom:8,bradi:5,brain:[0,3,5,8],brain_mask:[0,3],bridg:[],brows:0,bu:[],bucket:[],bz2:[],bz:[],c3d:[],c:[3,5,7],ca:[],cab:[],calc_friston:[],calc_friston_twenty_four:0,calcul:[0,3,5],calculate_connect:13,calculate_fd_jenkinson:0,calculate_fd_pow:[],call:7,can:[0,3],carp:5,carpet:[0,5,8],carpet_plot:[0,5,12],caudn:[],caudn_d:[],caudn_v:[],caudnh_nacc:[],caution:[0,5],cc:[],cd:[],ceagent:[],censor:5,center:[],cer5:[],cer6_a:[],cer6_d:[],cer6_p:[],cer7ab:[],cer7b_l:[],cer7b_m:[],cer9_d:[],cer9_m:[],cer9_v:[],cer:[],cercr1:[],cervm:[],cgm:[],chang:0,check:[0,3,5],check_output:[],choos:3,choosen:7,chosen:3,clean_data:8,close:[],closest:3,cmap:[0,8],cmdline:[],cngsul_p:[],coarse_search:[],code:[3,5],collaps:[],collect_predict:13,color:8,colorbar:0,colormap:0,colsul:[],column:0,com:[0,1,3,5,7,8],combin:[],command:1,commandlin:1,commandlineinputspec:1,common:[],commun:[],community_pycharm:[],compcor:[0,2],compcor_qc:5,complet:[],complic:[],compon:5,composit:5,comput:0,concat:[0,2],concat_xfm:[],concaten:[0,5],conf:[],config:0,confound:[],connect:[0,5],consid:0,contain:[0,5],content:[],continu:0,contour:[],converg:[],convert:[],convert_xfm:[],corder:[],core:1,coregistr:[0,3],corratio:[],correct:[0,3,5],correl:5,cost:[],cost_func:[],count:[],cox:[],cpac:[3,5],cpio:[],creat:[0,3,5],create_anat_noise_roi_workflow:5,create_coregistration_qc:0,create_segmentation_qc:0,creds_path:[],crop_list:[],csf:3,csv:[],cuda:[],current:[0,8],cut_coord:0,cwd:8,d6e9:[],d:5,data:[0,5,8],data_censor:[0,2],data_in:[],data_rol:[],data_roll_squar:[],data_squar:[],datacens_workflow_threshold:5,datafram:[],dataset:[],datatyp:[],dbus_session_bus_address:[],de:5,de_d:[],deal:7,deb:[],debian_chroot:[],deconfound:[0,2],decor:0,deeper:3,def:[],defac:3,deface_mask:3,defacing_ex_bid:12,default_regexp_sub:0,default_valu:[],defin:[],definit:[],degre:[],delimit:[],deobliqu:[],depend:0,deprec:[],deriv:[],design_fil:5,desir:0,desktop:[],desktop_sess:[],desktop_startup_id:[],despik:[],despiking_afni:5,despiking_bids_ex:12,detail:[],determin:5,detrend:8,dev:[],df:[],di:[],did:[],differ:[],dilat:[],dilm:[],dim:0,dimens:[],dimension:[],dir:0,direct:[],directori:[0,8],dispik:5,displac:5,displai:0,display_init:[],display_mod:0,distribut:[],divid:[],dkfz:1,dl:[],dmax:[],dmnet:[],dmpfc_ar:[],dmpfcor_ac:[],dmpfcor_p:[],doc:[0,3,5,7],document:0,docutil:[],docutilsconfig:[],doe:[0,3],dof:[],doi:5,don:0,draw_cross:0,drop:0,drop_first_lin:0,dset:[],dtype:[],due:[],durat:[],dvis_:[],dvis_vl:[],dwi:[0,2,12],dwm:[],dz:[],e:[0,3,5,8],each:[],ear:[],easili:0,echo:[],echospac:[],edit:[],eig:[],either:[3,5],elaps:[],element:[],elif:[],els:[],emf:[],en:3,en_u:[],encrypt_bucket_kei:[],engin:12,environ:[],ero:[],error:[],esd:[],essen:5,estim:[],et:5,etc:0,everi:0,everyth:7,ex:[],ex_aft:5,ex_befor:5,ex_bids_pipelin:12,ex_compcor:12,ex_func_proc:12,ex_func_to_anat_bid:12,ex_motion_correct:12,ex_pipelin:5,ex_tmpfilt:12,exampl:[0,11,12],except:[],exclud:5,exec:[],execut:0,extens:0,extra_deriv:[],extra_indic:[],extract:[0,3,7],f2guxnt:[],f:[],factor:[],fallback:0,fals:[0,1,3,8],fast:3,fast_csf:[],fast_gm:[],fast_mixeltyp:[],fast_prob_0:[],fast_prob_0_math:[],fast_prob_0_maths_math:[],fast_prob_1:[],fast_prob_1_math:[],fast_prob_2:[],fast_prob_2_math:[],fast_pve_0:[],fast_pve_1:[],fast_pve_2:[],fast_pveseg:[],fast_pveseg_plot:[],fast_wm:[],fcp:[3,5,7],fd:5,fd_averag:[],fd_figur:5,fd_file:5,fd_mode:5,fd_power_2012:[],fd_scrub:5,fd_scrubbed_fil:[],fdmax:5,fef:[],few:0,field:[3,7],fieldmap:3,fieldmapmask:[],figdpi:[],figsiz:[],figur:[0,5],file:[0,3,5,13],filelist:[],filenam:0,fill:[],filter:5,fine_search:[],finish:[],first:[5,7],fit:[],fix_scale_skew:[],flac:[],flatpak:[],flatten:0,flc:[],fli:[],flip:[],flirt:3,float32:[],float64:[],flv:[],fmap:[],fmri:3,fmrib:3,fname:[0,5],fnirt_config:0,folder:0,follow:[],forc:3,force_sc:[],format:[],found:0,four:0,fp:[],fpnet_visdn:[],frac:[],fraction:8,frame:[0,5],frames_aft:0,frames_befor:0,frames_in_1d_fil:0,frames_in_idx:[],frames_in_idx_str:[],frames_out:[],frames_out_idx:[],framewis:5,framewisedisplac:[],friston24:5,friston24_fil:5,friston:0,fristons_twenty_four:[],from:[0,3,5,7,8],fsl:[0,3,5],fsl_tsplot:[],fsldir:[],fslgecudaq:[],fsllockdir:[],fslmachinelist:[],fslmath:[],fslmeant:[],fslmultifilequit:[],fsloutputtyp:[],fslremotecal:[],fslreorient2std:[3,5],fslroi:[],fsltclsh:[],fslwiki:3,fslwish:[],full:3,func2anat:5,func:[0,2,3,12],func_align:5,func_out_fil:5,func_preproc:5,func_proc:[0,2],func_proc_despike_afni:5,func_to_anat:[0,2],funcpipelin:0,function_str:[],further:0,fusgyr_dl:[],fusgyr_vl:[],futur:[],fwhm:5,g:[0,3,5],gail:[],game:[],gcc64:[],gdm:[],gdmsession:[],gener:[0,3,5,8],generate_motion_statist:5,genfromtxt:[],get:[0,7],get_config:0,get_data:[],get_indx:0,get_info:7,get_ref_from_templateflow:0,get_ref_loc:0,get_refer:0,get_repetition_tim:[],get_rpn_model:12,get_scan_info:[],getcwd:[],gif:[],gio_launched_desktop_fil:[],gio_launched_desktop_file_pid:[],gist:[],github:[0,1,3,5,7,8],given:[0,7],gjs_debug_output:[],gjs_debug_top:[],gl32:[],gl:[],global:0,global_sign:0,gm:3,gnome:[],gnome_desktop_session_id:[],gnome_shell_session_mod:[],gnupg:[],go:0,gpg:[],gpg_agent_info:[],grab:[],grai:8,greater:7,grouppipelin:0,gtk_modul:[],gz:[0,3],gz_ab:[],gz_rel:[],gz_rot:[],gz_tran:[],h5:[],h:[],ha:0,hard:3,have:0,hd:[1,3],hdbet:[0,12],hdbetinputspec:1,hdbetoutputspec:1,head:[0,3],header:0,help:[],here:[0,5],hh:10,hierarchi:[],highpass:5,hipp:[],histogram:[],home:[],hostnam:[],hrb2ymenfw3feybrcgfx5sdmhs_2oh2l7:[],hsgyr:[],html:[0,3],http:[0,1,3,5,7,8],hyper:[],hz:5,i:8,ibu:[],ic:[],id:[],ignor:8,im:[],im_config_phas:[],imag:[0,3,5,8],image_manipul:[0,2],img:8,img_typ:[],improv:5,imsul:[],in_fil:[0,3,5,7],in_file2:[],in_matrix_fil:[],in_sourc:[],in_weight:[],includ:0,index:[0,5,7],index_deriv:[],indi:[3,5,7],indices_out:[],individual_gm_labelmap:0,infil:3,info:[0,2,5],inform:[0,1],ini:0,init:[],init_seg_smooth:[],init_transform:[],initi:[],inlist:[],input:[0,1,3,5,7],input_imag:[],input_image_typ:[],input_output:0,input_spec:1,inputspec_field:0,insert:[],inset:[],insight:3,inskull_mask_fil:[],inskull_mesh_fil:[],instal:[],instead:0,int32:[],integ:7,intend:[],intens:[0,8],interfac:[0,3,12],internal_datatyp:[],interp:[],interpol:[],interpolation_paramet:[],introduc:0,inv:[],inv_linear_reg:[],invers:[],invert_transform_flag:[],invert_xfm:[],invocation_id:[],io:[0,3],isdigit:[],isfil:[],iter:0,iterfield:0,iters_afterbia:[],itersourc:0,itgyr:[],itself:[7,8],j:5,jar:[],jediterm:[],jenkinson:5,jetbrain:[],join:[],jonathan:[0,8],journal_stream:[],jpeg:[],jpg:[],js:[],jul:[0,8],just:0,k:5,kei:0,keyr:[],kinc:3,kincs:[3,5],kmp_duplicate_lib_ok:[],kmp_init_at_fork:[],know:0,known:8,kwarg:[0,1,3,5,7,13],l:5,l_anggyr:[],l_cercr2_a:[],l_cercr2_p:[],l_dvis_v:[],l_fp_l:[],l_ifsul:[],l_iplob:[],l_ipsul:[],l_mfgyr_a:[],l_mfgyr_pc:[],l_mfgyr_pr:[],l_motnet_dl:[],l_mtgyr_a:[],l_mtgyr_p:[],l_pcsul:[],l_sfsul_a:[],l_vlpfcor:[],label:0,labelmap:0,lang:[],laplac:[],last:[3,5,7],later:5,latest:3,lc_address:[],lc_identif:[],lc_measur:[],lc_monetari:[],lc_name:[],lc_numer:[],lc_paper:[],lc_telephon:[],lc_time:[],learn:[],legend_fil:[],len:[],length:[],lessclos:[],lessopen:[],lesspip:[],level:0,lha:[],lib:[],light:3,like:[0,8],limnet:[],lin_mat:[],line:0,linear:5,linear_func_to_anat:[],linear_reg:[],linearsegmentedcolormap:[],linewidth:0,linux:[],list:0,listdir:[],ln:[],load:[],load_layout:[],loadtxt:[],local:0,local_copi:[],locat:0,log:[],lognam:[],look:0,lookup:[],lorbgyr:[],lowercas:0,lowpass:5,lrz:[],ls_color:[],lut:[],lvisnet_dp:[],lvisnet_p:[],lvisnet_vp:[],lz4:[],lz:[],lzh:[],lzma:[],lzo:[],m2v:[],m4a:[],m4v:[],m:5,ma:[],mad:[],made:0,mai:[],main:[3,5],make:[],make_termerr:[],make_termout:[],makeflag:[],makelevel:[],managerpid:[],manipulating_imag:0,manual:[],manual_seg:[],map:[3,8],mapnod:0,mask:[0,3,5,7,8],mask_fil:5,master:[],mat:[],mat_0000:[],mat_0001:[],mat_0002:[],mat_0003:[],mat_0004:[],mat_0005:[],mat_0006:[],mat_0007:[],mat_0008:[],mat_0009:[],mat_0010:[],mat_0011:[],mat_0012:[],mat_0013:[],mat_0014:[],mat_0015:[],mat_0016:[],mat_0017:[],mat_0018:[],mat_0019:[],mat_0020:[],mat_0021:[],mat_0022:[],mat_0023:[],mat_0024:[],mat_0025:[],mat_0026:[],mat_0027:[],mat_0028:[],mat_0029:[],mat_0030:[],mat_0031:[],mat_0032:[],mat_0033:[],mat_0034:[],mat_0035:[],mat_0036:[],mat_0037:[],mat_0038:[],mat_0039:[],mat_0040:[],mat_0041:[],mat_0042:[],mat_0043:[],mat_0044:[],mat_0045:[],mat_0046:[],mat_0047:[],mat_0048:[],mat_0049:[],mat_0050:[],mat_0051:[],mat_0052:[],mat_0053:[],mat_0054:[],mat_0055:[],mat_0056:[],mat_0057:[],mat_0058:[],mat_0059:[],mat_0060:[],mat_0061:[],mat_0062:[],mat_0063:[],mat_0064:[],mat_0065:[],mat_0066:[],mat_0067:[],mat_0068:[],mat_0069:[],mat_0070:[],mat_0071:[],mat_0072:[],mat_0073:[],mat_0074:[],mat_0075:[],mat_0076:[],mat_0077:[],mat_0078:[],mat_0079:[],mat_0080:[],mat_0081:[],mat_0082:[],mat_0083:[],mat_0084:[],mat_0085:[],mat_0086:[],mat_0087:[],mat_0088:[],mat_0089:[],mat_0090:[],mat_0091:[],mat_0092:[],mat_0093:[],mat_0094:[],mat_0095:[],mat_0096:[],mat_0097:[],mat_0098:[],mat_0099:[],mat_0100:[],mat_0101:[],mat_0102:[],mat_0103:[],mat_0104:[],mat_0105:[],mat_0106:[],mat_0107:[],mat_0108:[],mat_0109:[],mat_0110:[],mat_0111:[],mat_0112:[],mat_0113:[],mat_0114:[],mat_0115:[],mat_0116:[],mat_0117:[],mat_0118:[],mat_0119:[],mat_0120:[],mat_0121:[],mat_0122:[],mat_0123:[],mat_0124:[],mat_0125:[],mat_0126:[],mat_0127:[],mat_0128:[],mat_0129:[],mat_0130:[],mat_0131:[],mat_0132:[],mat_0133:[],mat_0134:[],mat_0135:[],mat_0136:[],mat_0137:[],mat_0138:[],mat_0139:[],mat_0140:[],mat_0141:[],mat_0142:[],mat_0143:[],mat_0144:[],mat_0145:[],mat_0146:[],mat_0147:[],mat_0148:[],mat_0149:[],mat_0150:[],mat_0151:[],mat_0152:[],mat_0153:[],mat_0154:[],mat_0155:[],mat_0156:[],mat_0157:[],mat_0158:[],mat_0159:[],mat_0160:[],mat_0161:[],mat_0162:[],mat_0163:[],mat_0164:[],mat_0165:[],mat_0166:[],mat_0167:[],mat_0168:[],mat_0169:[],mat_0170:[],mat_0171:[],mat_0172:[],mat_0173:[],mat_0174:[],mat_0175:[],mat_0176:[],mat_0177:[],mat_0178:[],mat_0179:[],mat_0180:[],mat_0181:[],mat_0182:[],mat_0183:[],mat_0184:[],mat_0185:[],mat_0186:[],mat_0187:[],mat_0188:[],mat_0189:[],mat_0190:[],mat_0191:[],mat_0192:[],mat_0193:[],mat_0194:[],mat_0195:[],mat_0196:[],mat_0197:[],mat_0198:[],mat_0199:[],mat_0200:[],mat_0201:[],mat_0202:[],mat_0203:[],mat_0204:[],mat_0205:[],mat_0206:[],mat_0207:[],mat_0208:[],mat_0209:[],mat_0210:[],mat_0211:[],mat_0212:[],mat_0213:[],mat_0214:[],mat_0215:[],mat_0216:[],mat_0217:[],mat_0218:[],mat_0219:[],mat_0220:[],mat_0221:[],mat_0222:[],mat_0223:[],mat_0224:[],mat_0225:[],mat_0226:[],mat_0227:[],mat_0228:[],mat_0229:[],mat_0230:[],mat_0231:[],mat_0232:[],mat_0233:[],mat_0234:[],mat_0235:[],mat_0236:[],mat_0237:[],mat_0238:[],mat_0239:[],mat_0240:[],mat_0241:[],mat_0242:[],mat_0243:[],mat_0244:[],mat_0245:[],mat_0246:[],mat_0247:[],mat_0248:[],mat_0249:[],mat_0250:[],mat_0251:[],mat_0252:[],mat_0253:[],mat_0254:[],mat_0255:[],mat_0256:[],mat_0257:[],mat_0258:[],mat_0259:[],mat_0260:[],mat_0261:[],mat_0262:[],mat_0263:[],mat_0264:[],mat_0265:[],mat_0266:[],mat_0267:[],mat_0268:[],mat_0269:[],mat_0270:[],mat_0271:[],mat_0272:[],mat_0273:[],mat_0274:[],mat_0275:[],mat_0276:[],mat_0277:[],mat_0278:[],mat_0279:[],mat_0280:[],mat_0281:[],mat_0282:[],mat_0283:[],mat_0284:[],mat_0285:[],mat_0286:[],mat_0287:[],mat_0288:[],mat_0289:[],mat_fil:5,match:[],matplotlib:[0,5,8],matric:5,matrix:[3,5],matt:[],matter:5,max:[0,8],max_fil:[],max_from_txt:0,maxfd:[],maximum:0,mayb:[],mc_first24:[],mc_func:[],mc_par:[],mc_par_fil:5,mc_rm:[],mc_rotat:[],mc_timeseri:[],mc_translat:[],mcflirt:5,mdvisnet_a:[],mdvisnet_p:[],me:[],mean:[0,5,7],mean_fil:[],mean_from_txt:0,mean_img:[],mean_t:[],mean_vol:[],meanfd:[],mem_gb:0,mesh:[],meshfil:[],method:[0,5],methodnam:14,metric:[],mflag:[],mh:[],mi:[],mic:1,mid:[],middl:[3,5,7],midi:[],min:8,min_sampl:[],mist:0,mist_122:[],mist_directori:0,mist_label:0,mist_modul:0,mixel_smooth:[],mixeltyp:3,mjpeg:[],mjpg:[],mka:[],mkv:[],mm:[],mng:[],mni152_t1_2mm:0,mni152_t1_2mm_brain:0,mni152_t1_2mm_ventriclemask:[],mni152_t1_2mm_ventriclemask_resampl:[],mni152_t1_2mm_ventriclemask_resample_tran:[],mni152lin:0,mni152lin_r:0,mo:[],mo_time37591:[],modal:[],model:[],model_json:13,modif:0,modifi:[3,5],modul:[2,12],morbgyr:[],more:[0,1],mosaic:0,motion:[0,5],motion_correct:5,motion_correction_mcflirt:5,motioncorrect:5,motnet:[],motnet_am:[],motnet_l:[],motnet_m:[],motnet_ml:[],motnet_vl:[],mov:[],move:[],movement:0,mp3:[],mp4:[],mp4v:[],mpc:[],mpeg:[],mpg:[],mri:5,mt:[],multimod:[0,2,12],multipl:[],must:0,mute:[],mvisnet_ad:[],mvisnet_av:[],mvisnet_p:[],mybet:[],mymc:[],myonevol:[],n:[],n_proc:0,name:[0,3,5,7],nan2zero:[],nb:[],ndarrai:0,nearest:0,necessari:[0,3],need:[0,3],needed_output:0,nest:0,nestedmapnod:0,nestednod:0,nestedworkflow:0,network:5,neuroimag:[0,5,8],new_data:[],new_fil:0,new_label:0,newdata:[],newlabel:[],newlabels_fil:[],nib:[],nibabel:[],nifti1imag:[],nifti:[],nifti_datatyp:[],nifti_gz:[],nii:[0,3],niimg:8,nilearn:0,nipyp:[0,1,3],nipype_no_et:[],niworkflow:[0,8],nn:[],nnerror:[],no_bia:[],no_clamp:[],no_output:[],no_pv:[],no_resampl:[],no_resample_blur:[],no_search:[],nobin:[],node:[0,13],nois:5,non:7,none:[0,1,3,8,13],normal:[],note:[0,8],noth:7,nov:[],np:[],npossibl:[],nslot:[],nuisanc:5,nuisance_remov:5,nuissanc:5,nuissremov_workflow:5,num_thread:[],number:7,number_class:[],numpi:0,nuv:[],nvol:[],o:[],object:[0,8],obliqu:[],occrect:5,occtgyr_l:[],occur:0,oga:[],ogg:[],ogm:[],ogv:[],ogx:[],okai:0,old:[0,5],oldpwd:[],omat:[],omit:0,onc:[],one:[3,5],onli:[0,3,7,13],op_str:[],open:[],openmp:[],optim:5,option:0,opu:[],order:0,org:0,orient:3,orthoslic:0,os:[],other:0,other_prior:[],otherwis:[0,3],ouput:3,out1:[],out2:[],out3:[],out:5,out_basenam:[],out_data_typ:[],out_figur:[],out_fil:[0,3,5],out_log:[],out_matrix_fil:[],out_postfix:[],outfil:0,outlabelmap:0,outlin:[],outline_fil:[],output:[0,3,5],output_biascorrect:[],output_biasfield:[],output_datatyp:[],output_dir:0,output_fil:[0,8],output_imag:[],output_queri:0,output_spec:1,output_typ:[],outputspec_field:0,outputtyp:[],outskin_mask_fil:[],outskin_mesh_fil:[],outskull_mask_fil:[],outskull_mesh_fil:[],overlai:[0,3,7],overwrit:0,ow:[],ox:3,p:5,pac:[3,5,7],packag:[11,12],pad:[],padding_s:[],page:[],panda:[],par:0,par_fil:[],param:[0,5],paramet:[0,3,5,7,8],parameter:[],parameter_sourc:[],parcel:[],parfil:[0,5],part:5,partial:3,partial_volume_fil:[],partial_volume_map:3,partvol_map:3,parvol_csf:3,parvol_gm:3,parvol_wm:3,pass:0,path:[0,3,5,7,8],pbm:[],pca:0,pccor:[],pcsul_d:[],pcx:[],pd:[],pdf:0,pedir:[],percent:5,percent_scrub:[],percent_scrubbed_fil:[],percentfd:[],perform:[0,3,5],petersen:5,pgaccor:[],pgm:[],pi:[],pick_volum:7,pins_d:[],pins_v:[],pipelin:[0,11,12],pisul:[],pixdim:[],place:3,plat:[],plot:[0,5,12],plot_carpet:8,plot_carpet_t:0,plot_finish:[],plot_motion_tran:5,plot_rang:[],plot_roi:0,plot_siz:[],plot_start:[],plot_typ:7,plottimes:[],plu:0,plumb:[],png:[0,5],point:[],poldracklab:[0,8],porcupin:5,posit:3,possibl:[0,7],post:[],posul:[],posul_d:[],posul_v:[],power:[0,5,8],powersfd_data:[],ppm:[],prc_d:[],prc_v:[],preced:[],predict_pain_sensit:13,prefix:[],preprocess:3,prev_wd:[],princip:5,print:[],print_out_composite_warp_fil:[],prior:3,priormap:3,probability_map:[],probabl:3,probmap_csf:3,probmap_gm:3,probmap_wm:3,proc:[],proces:[],process:[3,5],provid:8,ps1:[],psc:8,psmcor_a:[],psmcor_p:[],pt:[],pumi:13,pumipipelin:0,put_a:[],put_p:[],pvisnet_dm:[],pvisnet_l:[],pvisnet_vm:[],pwd:[],py:[3,5],pycharm:[],pycharmproject:[],pydeface_wrapp:3,pythonpath:[],q:[],qc:[3,5],qc_anat2mni:[],qc_background:[],qc_datacen:5,qc_motion_correct:[],qc_motion_correction_mcflirt:5,qc_nuisance_remov:5,qc_overlai:[],qc_segment:3,qc_temporal_filt:5,qc_tissue_segment:3,qcpipelin:0,qt:[],qt_access:[],qt_im_modul:[],qualiti:[0,3,5],queri:0,r:[],r_anggyr:[],r_cercr2_a:[],r_cercr2_p:[],r_dvis_v:[],r_fp_l:[],r_ifsul:[],r_iplob:[],r_ipsul:[],r_mfgyr_a:[],r_mfgyr_p:[],r_motnet_dl:[],r_mtgyr_a:[],r_mtgyr_p:[],r_pcsul:[],r_porb:[],r_sfsul:[],r_vlpfcor:[],ra:[],radian:[],radiu:[],rais:[],raise_on_empti:[],rang:[],rar:[],rate:[],readthedoc:3,realign:5,reconstruct:[],record:3,reduce_bia:[],reduct:5,ref:0,ref_brain:3,ref_brain_mask:3,ref_fil:[],ref_head:3,ref_vol:[],ref_weight:[],refer:[0,5],reference_brain:0,reference_head:0,reference_imag:[],reference_vol:5,reffil:[],refvol:[],reg_timeseri:0,reg_tool:3,regcmd:[],regexp_sub:0,regexp_substitut:[],regist:3,registered_brain:0,registered_brain_filenam:[],registr:[3,5],registration_ants_hardcod:0,regress:5,regressor:5,regt:0,regular:[],rel:[0,5],relabel:0,relabel_atl:[],relabel_atla:0,relabel_fil:0,relabeld:0,relabeled_atla:[],relabeled_atlas_resampl:[],relabelled_atlas_fil:[],releas:[],remov:[5,8],remove_dest_dir:[],remove_ey:[],reorder:0,reordered_label:0,reordered_modul:0,reorient:[3,5],reorient_func_wf:[],reorient_struct_wf:[],repertoir:0,repetit:[],repetition_tim:[],repli:5,represent:[0,8],request:7,resample_atla:[],resample_mod:[],resample_std_ventricl:[],resampling_interpol:0,reset_index:[],resolut:0,respect:0,rest:5,rest_bold:[],rest_bold_reori:[],rest_bold_reoriented_brain:[],rest_bold_reoriented_brain_mask:[],rest_bold_reoriented_brain_mask_roi:[],rest_bold_reoriented_mask:[],rest_bold_reoriented_masked_mcf:[],rest_bold_reoriented_masked_mcf_despik:[],rest_bold_reoriented_masked_mcf_math:[],rest_bold_reoriented_masked_mcf_t:[],rest_bold_reoriented_masked_roi:[],rest_bold_reoriented_roi:[],rest_bold_reoriented_roi_flirt:[],rest_bold_reoriented_roi_plot:[],restored_imag:[],result:[0,5],ret:[],right:7,rigid2d:[],rigid:5,rm:[],rms_file:[],rmsab:[],rmsrel:[],rmvb:[],robust:5,roi:[5,7],roi_fil:[],roi_img:0,roll:[],rotat:5,round:[],row:0,rpm:[],rpn:[],rpn_model:0,rpn_preproc:12,rpn_signatur:12,rs:[],run:[0,7],run_without_submit:0,runtest:14,rw:[],rz:[],s:[0,5],sai:[],same:[],sar:[],satra:[],save:[0,5,8],save_carpet:8,save_img:0,save_log:[],save_mat:[],save_plot:[],save_rm:[],savefig:[],savetxt:[],sbin:[],scale:[],scale_vol:0,scaled_fil:[],scaled_func:[],scan:[],schedul:[],schema:0,schlaggar:5,sci_not:[],script:5,scrub:[0,5],scrub_imag:0,scrub_input:0,scrub_input_str:0,scrubbed_imag:[0,5],search:[0,13],searchr_i:[],searchr_x:[],searchr_z:[],second:5,section:0,see:[0,5,8],seg_preproc:3,segment:[0,2],segment_it:[],select:0,sep:[],sequenc:7,seri:[],serial:0,series_tr:[],session:[],session_manag:[],set:[0,3,8],setdiff1d:[],sfgyr_ad:[],sg:[],shape:[],share:[],shell:[],shlvl:[],should:[0,3,5,8],show:8,show_al:[],show_carpet:8,shrink:[],sigma:[],signal:8,simplify_list:[],sinc_width:[],sinc_window:[],singl:[],sink:[3,5,7],sinker:3,skiprow:[],skull:[],skull_fil:[],skull_mask_fil:[],slice:[5,7],small:0,smaller:8,smash:[],smgyr:[],smith:5,smooth:[],snap:[],snap_arch:[],snap_common:[],snap_context:[],snap_cooki:[],snap_data:[],snap_instance_kei:[],snap_instance_nam:[],snap_library_path:[],snap_nam:[],snap_real_hom:[],snap_reexec:[],snap_revis:[],snap_user_common:[],snap_user_data:[],snap_vers:[],snapd:[],snyder:5,so:0,some:0,someth:0,sort:[],sort_valu:[],sourc:[0,1,3,5,7,8,10,13,14],space:[3,5],spatial:3,spatial_coord:[],spec:1,specif:0,specifi:[0,7],spike:5,spisak:[3,5],spline:[],spline_fin:[],split:[],splob:[],spuriou:5,spx:[],squeez:[],ssh:[],ssh_agent_pid:[],ssh_auth_sock:[],st:[],stage:[],stai:[0,8],stand2anat_xfm:3,standard2input:3,standard:[0,3,8],standardis:3,start:[0,7],start_idx:7,startswith:[],state:5,stats_img:[],std:[],std_brain:3,std_img:[],stderr:[],stdrefvol:5,step:5,stgyr_a:[],stgyr_m:[],stgyr_p:[],store:[3,8],str:[0,3,5,7,8],strategi:8,string:0,strip_dir:[],su:[],sub:7,subjacet:3,subject:[3,5],submodul:12,subpackag:[0,2],subplot:0,subprocess:[],substitut:0,successfulli:[],suffix:[],suitabl:0,sure:[],surfac:[],svg:0,svgz:[],swap:[],swm:[],syn:[],synchron:0,systemat:5,t1w:3,t2_guid:[],t7z:[],t:0,t_min:[],t_size:[],tab10:0,tabl:[],tama:[3,5],tar:[],task:[],taz:[],tbz2:[],tbz:[],templat:0,templateflow:0,tempor:5,temporal_filt:[0,2],term:[],term_session_id:[],terminal_emul:[],terminal_output:1,test:[11,12],test_afni:12,test_ant:12,test_despik:14,test_fsl:12,testant:14,testcas:14,testdespik:14,testfsl:14,text:[0,5],tf:0,tga:[],tgz:[],thal_d:[],thal_v:[],than:[7,8],them:[],thi:[0,7],thirdli:5,those:5,thr:[],thread:[],threshold:[0,5,8],through:8,thrown:7,tif:[],tiff:[],time:[0,3,5,8],timecourse2png:7,timefram:8,timepoint:[],timeseri:[0,5],tissu:[0,3],tissue_class_fil:[],tissue_class_map:[],tissue_segmentation_fsl:3,titl:0,tlz:[],tmp:[],to_csv:[],todo:[0,3,5,7],todo_readi:[],tolist:[],tool:3,toolbox:[],top:[0,8],toward:5,tp:[],tpl:0,tr:[],traitedspec:1,transform:5,transform_composit:[],transform_inverse_composit:[],transform_warp:[],transform_warped_plot:[],transformcomposit:[],transforminversecomposit:[],translat:5,transpos:[],tri:0,truncat:[],tsextractor:0,tsv:0,tw:[],twenti:0,txt2maxtxt:0,txt2meantxt:0,txt:[0,5],txz:[],type:[0,3,7,8],tz:[],tzo:[],tzst:[],u:[],ubuntu:[],uk:[3,5],undefin:[],unexist:[],unittest:14,unix:[],unlik:0,unwarp_ventricl:[],up:5,upper:5,us:[0,3,5,7,8,13],use_contour:[],use_gradi:[],use_mm:[],use_prior:[],user:[3,7],usernam:[],uses_qform:[],usr:0,utf:[],util:12,valid:[0,7],valu:[0,7,8],valueerror:[],valueexcept:7,variabl:5,variance_img:[],vattnet_salnet_bg_th:[],ventricl:5,ventricle_mask:[0,5],venv:[],verbos:[],version:[3,5],vertical_gradi:[],view:[],view_typ:0,virtual_env:[],visnet:[],vloum:3,vmax:0,vmin:0,vmpfcor_a:[],vmpfcor_p:[],vob:[],vol2png:7,vol_count:[],volum:[0,3,5,7],vox:7,vox_roi:[],voxel:[0,7,8],voxel_s:[],vvisnet_l:[],vvisnet_m:[],w:[],wa:[0,3,5,7,8],want:[0,3],war:[],warn:[],warp:3,warped_imag:[],wav:[],we:[0,7],weather:8,webm:[],wf:[0,3,5,7,13],what:[],when:[3,13],where:0,which:[0,3,5,7,8],white:5,why:[],wim:[],windowpath:[],winsor:[],winter:0,wise:5,within:0,without:0,wm:3,wm_mask:5,wm_seg:[],wmcoord:[],wmnorm:[],wmseg:[],wmv:[],work:[0,8,13],workaround:3,workflow:[0,3,5,7],working_dir:[],would:0,wrapper:[0,1],write:[],write_cmdlin:1,www:0,x11:[],x86_64:[],x:[7,8],x_min:[],x_precis:[],x_size:[],x_unit:[],xauthor:[],xbm:[],xcf:[],xdg:[],xdg_config_dir:[],xdg_current_desktop:[],xdg_data_dir:[],xdg_menu_prefix:[],xdg_runtime_dir:[],xdg_session_class:[],xdg_session_desktop:[],xdg_session_typ:[],xmodifi:[],xpm:[],xspf:[],xterm:[],xwd:[],xz:[],y:[7,8],y_max:[],y_min:[],y_rang:[],y_size:[],yagtshcbsu:[],ye:[],you:[0,3],yuv:[],z:[5,7,8],z_min:[],z_size:[],zero:7,zip:[],zoo:[],zscore:8,zst:[]},titles:["PUMI package","PUMI.interfaces package","PUMI.pipelines package","PUMI.pipelines.anat package","PUMI.pipelines.dwi package","PUMI.pipelines.func package","PUMI.pipelines.func.info package","PUMI.pipelines.multimodal package","PUMI.plot package","definitions module","examples package","Welcome to PUMI\u2019s documentation!","PUMI","pipelines package","tests package"],titleterms:{above_threshold:[],afni:[],anat2mni:3,anat2mni_ants_hardcod:[],anat2mni_ants_hardcoded_qc:[],anat:3,anat_proc:3,anatomical_preprocessing_wf:[],ant:[],ants_hardcod:[],apply_mask:[],atlas2func_qc:[],atlas2func_vol2png:[],atlas2n:[],bbr_arg_convert:[],bbr_wf:[],bbreg_func_to_anat:[],bet:[],bet_bids_func_subworkflow:10,bet_bids_subworkflow:10,bet_fsl:[],bet_vol:[],bids_grabb:[],calc_friston:[],calculate_fd_pow:[],carpet_plot:8,censored_timeseri:[],compcor:5,compcor_qc:[],compcor_roi_wf:[],concat:5,conf:[],confound:[],content:11,csf_bb_mask:[],data_censor:5,deconfound:5,defacing_ex_bid:10,definit:9,despik:[],despiking_bids_ex:10,document:11,dwi:4,engin:0,environ:[],error:[],ex_bids_pipelin:10,ex_compcor:10,ex_func_proc:10,ex_func_to_anat_bid:10,ex_motion_correct:10,ex_tmpfilt:10,exampl:10,execut:[],extract_timeseri:[],fast:[],fsl:[],fslroi:[],func2anat_qc:[],func:[5,6],func_proc:5,func_proc_wf:[],func_to_anat:3,get_rpn_model:10,gm_bb_mask:[],hdbet:1,image_manipul:7,img_4d_info:[],indic:[],info:6,input:[],interfac:1,inv_linear_reg:[],io:[],linear_func_to_anat:[],linear_reg:[],maxfd:[],mc_timeseri:[],mcflirt:[],mean_t:[],meanfd:[],modul:[0,1,3,5,7,8,9,10,13,14],multimod:7,mybet:[],mycmpcor:[],myconc:[],mymc:[],mynuisscor:[],myonevol:[],myqc:[],myqc_datacen:[],myscrub:[],mytmpfilt:[],node:[],nuisance_removal_qc:[],origin:[],output:[],packag:[0,1,2,3,4,5,6,7,8,10,13,14],path_extractor_bold:[],path_extractor_t1w:[],pick_atlas_wf:[],pipelin:[2,3,4,5,6,7,13],plot:8,plot_motion_rot:[],plot_motion_tran:[],plottimes:[],pumi:[0,1,2,3,4,5,6,7,8,11,12],qc:[],qc_background:[],qc_mc:[],qc_overlai:[],qc_segment:[],refvol:[],relabel_atl:[],reorient_func_wf:[],reorient_struct_wf:[],resample_atla:[],resample_std_ventricl:[],rpn_preproc:10,rpn_signatur:13,runtim:[],s:11,scale:[],segment:3,sinker:[],split_partial_volume_fil:[],split_probability_map:[],standard:[],submodul:13,subpackag:5,tabl:[],tc2png_tmpfilt:[],temporal_filt:5,termin:[],test:[10,14],test_afni:14,test_ant:14,test_fsl:14,time_repetit:[],tissue_segmentation_fsl:[],unwarp_ventricl:[],util:0,vent_bb_mask:[],ventricle_mask:[],vox_roi:[],welcom:11,wm_bb_mask:[]}})