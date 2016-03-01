# gl_grumpv1_ntlbndid_grid_30/gluntlbnds comes from 9.7MB grid download at:
# http://sedac.ciesin.columbia.edu/data/set/grump-v1-national-identifier-grid/data-download
gluntlbnds.csv: gl_grumpv1_ntlbndid_grid_30/gluntlbnds
	./extract-lookup.py gl_grumpv1_ntlbndid_grid_30/gluntlbnds $@
