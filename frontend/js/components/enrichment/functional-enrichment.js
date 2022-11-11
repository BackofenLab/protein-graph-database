Vue.component("functional-enrichment", {
    props: ["gephi_json", "func_json","revert_term","func_enrichment", "reset_term"],
    data: function() {
        return  {
            filter_terms: {
                "RESET": "No Filter",
                "TISSUES": "Tissue expression",
                "KEGG": "KEGG Pathway",
                "COMPARTMENTS": "Subcellular localization",
                "Process": "Biological Process",
                "Component": "Cellular Component(Gene Ontology)",
                "Function": "Molecular Function",
                "Keyword": "Annotated Keywords(UniProt)",
                "SMART": "Protein Domains(SMART)",
                "InterPro": "Protein Domains and Features(InterPro)",
                "Pfam": "Protein Domains(Pfam)",
                "PMID": "Reference Publications(PubMed)",
                "RCTM": "Reactome Pathway",
                "WikiPathways": "WikiPathays",
                "MPO": "Mammalian Phenotype Ontology",
                "NetworkNeighborAL": "Network",
                
            },
            message: "",
            terms: [],
            saved_terms: [],
            proteins: [],
            search_raw: "",
            filter: "",
            await_check: true,
            await_load: false,
            term_numbers: "",

        }
    },
    methods: {
        select_term: function(term) {
            var com = this;
            com.$emit("active-term-changed", term);
        },
        select_cat: function(category) {
            var com = this;


            var filtered_terms = [];
            var check_terms = com.saved_terms[com.saved_terms.length -1];

            //Filter the terms according to user selection
            for (var idx in check_terms) {
                if(check_terms[idx].category == category && category != "RESET"){
                    filtered_terms.push(check_terms[idx]);
                }
            }
            //Reset function for Terms
            if(category != "RESET"){
                com.terms = filtered_terms;
            }else{com.terms = com.saved_terms[com.saved_terms.length -1]}

            //Count term number
            com.term_number();
        },
        get_functionterms: function(term) {
            var com = this;
            com.$emit("func-json-changed", term);
        },
        export_enrichment: function(){
            com = this;

            //export terms as csv
            csvTermsData = com.terms;
            terms_csv = 'category,fdr_rate,name,proteins\n';

            csvTermsData.forEach(function(row) {
                terms_csv += row['category'] + ',' + row['fdr_rate'] + ',"'  + row['name'] + '","' +row['proteins']+'"';
                terms_csv += '\n';   
            });


            //Create html element to hidden download csv file
            var hiddenElement = document.createElement('a');
            hiddenElement.target = '_blank';
            hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(terms_csv);
            hiddenElement.download = 'Terms.csv';  
            hiddenElement.click();
        },
        term_number: function(){
            var com = this;

            com.term_numbers = com.terms.length.toString();

        }
    },
    watch: {
        "gephi_json": function(json) {
            var com = this;
            if (!json) return ; //handling null json from backend
            // if (!json.enrichment) return: ‚
            
            com.get_functionterms(json.nodes);

        },
        "func_json": function(nodes) {
            var com = this;

            //Reverting functional terms
            if(nodes==null) {
                com.await_check = false, com.terms = com.saved_terms[0], com.saved_terms = [com.terms];
                com.term_number();
                return;
            }

            //Set up parameter for functional enrichment
            com.proteins = [];
            for (var idx in nodes) {
                com.proteins.push(nodes[idx].id);
            }
            
            com.await_check = true, com.await_load = true;
            formData = new FormData();
            formData.append('proteins', com.proteins);
            formData.append('species_id', nodes[0].species);
            
            
            //POST request for functional enrichment
            $.ajax({
                type: 'POST',
                url: "/api/subgraph/enrichment",
                data: formData,
                contentType: false,
                cache: false,
                processData: false,
              })
              .done(function (json) {         
                com.await_load = false;                  
                  if(com.await_check){
                      com.$emit("func-enrichment-changed", json);
                      //Save terms
                      com.terms = [];
                      for (var idx in json) {
                          com.terms.push(json[idx]);
                        }
                        com.saved_terms.push(com.terms);

                        //Sort terms according to the fdr rate
                        com.terms.sort(function(t1, t2) {
                            var p_t1 = parseFloat(t1.fdr_rate);
                            var p_t2 = parseFloat(t2.fdr_rate);
                            return p_t1 - p_t2;
                        });

                        //Count term number
                        com.term_number();
                    }
            });
        },
        "revert_term": function(subset) {
            var com = this;

            if (!subset) return ;

            //Load previous subset terms from saved_terms
            com.await_check = false;
            com.saved_terms.pop()
            com.terms = com.saved_terms[com.saved_terms.length-1];

            //Count term number
            com.term_number();
        },
        "reset_term": function(subset) {
            var com = this;

            if (!subset) return ;

            //Load main graph terms from saved_terms
            com.await_check = false;
            com.terms = com.saved_terms[0];

            //Count term number
            com.term_number();
        },
    },
    computed: {
        regex: function() {
            var com = this;
            return RegExp(com.search_raw.toLowerCase());
        },
        filtered_terms: function() {
            var com = this;

            if (com.search_raw == "") return com.terms;

            var regex = com.regex;
            var filtered = com.terms.filter(term => regex.test(term.name.toLowerCase()));
            return filtered;
        }
    },
    template: `
        <div v-show="gephi_json != null" id="enrichment" class="tool-pane">
            <div class="headertext">
            <h4>Functional enrichment:</h4>
            </div>
            <div class="main-section">
                <div class="enrichment-filtering">
                    <input type="text" value="Search functional terms by name" v-model="search_raw" class="empty"/>
                    <select v-model="filter" v-on:change="select_cat(filter)">
                        <option disabled value="">No Filter</option>
                        <option v-for="(value, key, index) in filter_terms" v-bind:value="key">{{value}}</option>
                    </select>
                </div>
                <div v-if="await_load==false" class="term_number">
                    <span>Terms: {{term_numbers}}</span>
                </div>
            <div v-if="await_load == true" class="loading_pane"></div>
            <div v-if="await_load == false" class="results">
                <i v-if="message.length > 0">{{message}}</i>
                <div v-for="entry in filtered_terms">
                    <a href="#" v-on:click="select_term(entry)">{{entry.name}}</a>
                </div>
                <div v-if="terms.length == 0">
                    <i>No terms available.</i>
                </div>
            </div>
            <button v-if="await_load == false" id="export-enrich-btn" v-on:click="export_enrichment()">Export</button>
        </div>
    </div>
    `
});