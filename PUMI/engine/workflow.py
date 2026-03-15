from nipype.pipeline.engine.workflows import *


class NestedWorkflow(Workflow):

    @property
    def inputs(self):
        """Proxy inputs from the inputspec node to support Nipype-style input access"""
        inputspec = self.get_node('inputspec')
        if inputspec is None:
            raise AttributeError("No inputspec node found in workflow")
        return inputspec.inputs

    def connect(self, *args, **kwargs):

        """
        Todo docs
        """

        # we convert the input to handle the subworkflow-shortcuts
        # (i.e. adding 'inoutspec.' and 'outputspec.' when needed)

        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError(
                "connect() takes either 4 arguments, or 1 list of"
                " connection tuples (%d args given)" % len(args)
            )

        connection_list = list(map(list, connection_list))

        # 1. Handle shortcut
        for i_conn_list, (srcnode, destnode, connects) in enumerate(connection_list):

            if isinstance(srcnode, str):
                connection_list[i_conn_list][0] = srcnode = self.get_node(srcnode)

            if isinstance(destnode, str):
                connection_list[i_conn_list][1] = destnode = self.get_node(destnode)

            for i_connects, (source, dest) in enumerate(connects):

                if isinstance(source, tuple):
                    # handles the case that source is specified
                    # with a function
                    sourcename = source[0]
                elif isinstance(source, (str, bytes)):
                    sourcename = source
                else:
                    raise Exception(
                        (
                            "Unknown source specification in "
                            "connection from output of %s"
                        )
                        % srcnode.name
                    )

                if sourcename and not srcnode._check_outputs(sourcename):
                    outputspec_source = 'outputspec.' + sourcename
                    if srcnode._check_outputs(outputspec_source):
                        connection_list[i_conn_list][2][i_connects] = (outputspec_source, dest)

                if not destnode._check_inputs(dest):
                    inputspec_dest = 'inputspec.' + dest
                    if destnode._check_inputs(inputspec_dest):
                        src = connection_list[i_conn_list][2][i_connects][0]
                        connection_list[i_conn_list][2][i_connects] = (src, inputspec_dest)
        # connect nodes
        super().connect(connection_list, **kwargs)
