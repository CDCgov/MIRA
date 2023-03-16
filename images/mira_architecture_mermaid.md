```mermaid
flowchart LR

BROWSER(<font size=5>- - - - -\nBROWSER\n- - - - - )

subgraph COMPOSE[<font size=3>Docker Compose]
subgraph DC1[<font size=3>Container]
MIRA[<font size=5>MIRA GUI]
end
subgraph DC2[<font size=3>Container]
IRMA[<font size=5>IRMA]
end
subgraph DC3[<font size=3>Container]
DAIS[<font size=5>DAIS-Ribosome]
end
subgraph DC4[<font size=3>Container]
CONFIG[[Run Configs]]
SPYNE[<font size=5>SPYNE]
CURATION[Curation, QC &\nFigure Generation]
end
end
subgraph FS[<font size=3>Local Filesystem]
DS((<font size=5>.   Docker   .\n.   Socket   .))
RESULTS[[<font size=5>Sequencing Files\nDirectory]]
end
MIRA === BROWSER
MIRA == Trigger ==> SPYNE
SPYNE <-. Orchestrate .-> IRMA
SPYNE <-. Orchestrate .-> DAIS
SPYNE <-. Orchestrate .-> CURATION
DC1 -.- DS
DC2 -.- DS
DC3 -.- DS
DC4 -.- DS
MIRA <==> RESULTS
IRMA <==> RESULTS
DAIS <==> RESULTS
SPYNE <==> RESULTS
CURATION <==> RESULTS
SPYNE -.- CONFIG

style BROWSER fill:#c994ff,color:#000000,stroke:#2e2e2e,stroke-width:12px
style SPYNE fill:#70d149,color:#000000,stroke:#333,stroke-width:5px
style CURATION fill:#70d149,color:#000000,stroke:#333,stroke-width:5px
style IRMA fill:#389114,color:#000000,stroke:#333,stroke-width:5px
style DAIS fill:#389114,color:#000000,stroke:#333,stroke-width:5px
style DC1 fill:#06a4d5,color:#000000,stroke-width:4px,stroke:#153b60
style DC2 fill:#06a4d5,color:#000000,stroke-width:4px,stroke:#153b60
style DC3 fill:#06a4d5,color:#000000,stroke-width:4px,stroke:#153b60
style DC4 fill:#06a4d5,color:#000000,stroke-width:4px,stroke:#153b60
style COMPOSE fill:#a8e5f7,color:#000000,stroke-width:4px,stroke:#153b60
style MIRA fill:#caffb5,color:#000000,stroke:#333,stroke-width:5px
style FS fill:#e0e0e0,color#000000,stroke:#000000,stroke-width:3px
style RESULTS fill:#fafafa,stroke:#000,stroke-width:2px
style DS fill:#fafafa,stroke:#000,stroke-width:2px
style CONFIG fill:#fafafa,stroke:#000,stroke-width:2px

```
