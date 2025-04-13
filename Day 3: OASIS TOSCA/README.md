# Introduction to OASIS TOSCA
Really need a good primer
***
## Dissecting OASIS TOSCA 
Whenever you are designing an application (system), answer the following questions for each and every component (piece of software you are using, scripts, databases, operating systems, hardware, etc.):
### TOSCA type categories:
| **Element** | **Purpose** |
| ----------- | ----------- |
| Node type | What you're deploying |
| Capability type | What it offers |
| Requirement | What it needs |
| Relationship | How it is linked with other components |
| Interface | What action it performs |
| Artifact | What you deploy |
| Data type | How data is structured |
| Policy | Runtime behavior |
| Group | Operate on multiple at once |

| **Type** | **What it is** | **Why it exists** | **Example** | **Section** |
| -------- | -------------- | ----------------- | ----------- | ----------- |
| `node_types` | Components of the system | You define software/hardware units | `tosca.nodes.WebServer` | 3.7 |
| `capability_types` | What a node _offers_ (e.g. hosting) | Enable connection point for requirements | `tosca.capabilities.Compute` | 3.8 |
| `requirement_types` | What a node _needs_ | Allows structured pluggability | e.g. `host` | 3.9 |
| `relationship_types` | How nodes _connect_ | Describes dependencies like `hosted_on`, `connected_to` | `tosca.relationships.HostedOn` | 3.10 |
| `interface_types` | _Actions_ a node can take | Defines lifecycle ops: create, configure, delete | `standard` interface | 3.11 |
| `artifact_types` | Forms of deployable data | e.g. script, docker image, zip file | `tosca.artifacts.File` | 3.12 |
| `data_types` | 
