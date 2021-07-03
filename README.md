# PUMI
Laboratory for Predictive Neuroimaging - University Hospital Essen, Germany


# Coding Conventions

- name of workflow is the same as the name of the variable that holds it
- name of node is the same as the name of the variable that holds it

- qc nodes's name defines the subdir in qc; it should be: <base_wf>_qc

- avoid "batch-connects" in @PumiPipeline funcions: it is preferred that right after node (or workflow) definition all possible connect statements corresponding to the node are specified 

- for readibility, we use the signature: connect(source_node, source_field, dest_node, dest_field)
- except, in case there are multiple connections between the same pair of nodes, batch-connect should be used


- @PumiPipeline funcions' first connect statement(s) is (are) connecting to the inputspec
- @PumiPipeline funcions' last connect statement(s) is (are) connecting to the outputspec


- @PumiPipeline funcions' are minimalistic and do NO "housekeeping".

# cite
- Isensee F, Schell M, Tursunova I, Brugnara G, Bonekamp D, Neuberger U, Wick A, Schlemmer HP, Heiland S, Wick W, Bendszus M, Maier-Hein KH, Kickingereder P. Automated brain extraction of multi-sequence MRI using artificial neural networks. Hum Brain Mapp. 2019; 1–13. https://doi.org/10.1002/hbm.24750
