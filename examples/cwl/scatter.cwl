cwlVersion: v1.2
class: Workflow
label: Toil WES smoke test
requirements:
  ScatterFeatureRequirement: {}
inputs:
  messages: string[]
outputs:
  greeting:
    type: string[]
    outputSource: hello/greeting
steps:
  hello:
    in:
      message: messages
    out: [greeting]
    scatter: message
    run:
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
