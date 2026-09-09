cwlVersion: v1.2
class: CommandLineTool
requirements:
  DockerRequirement:
    dockerPull: alpine:3.23
baseCommand: sleep
inputs:
  seconds:
    type: int
    default: 300
    inputBinding:
      position: 1
outputs: []
