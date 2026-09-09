cwlVersion: v1.2
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerPull: alpine:3.23
baseCommand: echo
inputs:
  message:
    type: string
    inputBinding:
      position: 1
stdout: greeting.txt
outputs:
  greeting:
    type: string
    outputBinding:
      glob: greeting.txt
      loadContents: true
      outputEval: $(self[0].contents)
