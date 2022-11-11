Vue.component("hubs", {
    props: ["gephi_json"],
    data: function() {
        return  {
            message: "",
            select_function: ["Hide Hubs", "Show Hubs"],
            selected_func: null
        }
    },
    methods: {
        get_hubs: function(state) {
            var com = this;
            let mean = 0;
            var subset = com.gephi_json.nodes.map(arrayItem => {
                return arrayItem.attributes["Degree"]
            });

            // ---mean calculation---

            // Convert String values to Integers
            var result = subset.map(function (x) { 
                return parseInt(x, 10);
            });
            let sum = result.reduce((accumulator, value) => {
                return accumulator + value;
            });

            mean = sum/subset.length;

            // ---empirical standard deviation---

            let stdDev = 0;
            stdDev = Math.sqrt(result.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / (subset.length - 1))

            // define threshold

            const treshold = Math.ceil(mean + stdDev)

            // filter hubs
            var nodes = [];
            for (var idx in com.gephi_json.nodes){
                if(com.gephi_json.nodes[idx].attributes["Degree"] < treshold && state == "Hide Hubs"){
                    nodes.push(com.gephi_json.nodes[idx])
                }
                if(com.gephi_json.nodes[idx].attributes["Degree"] >= treshold && state == "Show Hubs"){
                    nodes.push(com.gephi_json.nodes[idx])
                }

            

            com.$emit("active-subset-changed", nodes);
            /* array.filter(item => item.condition < 10)
            .forEach(item => console.log(item))*/
            }
        },
    },
    template: `
        <div v-show="gephi_json != null" class="toolbar-button">
            <div class="toolbar-theme">
                <select v-model="selected_func" v-on:change="get_hubs(selected_func)">
                    <option disabled value="">Please select function</option>
                    <option v-for="value in select_function">{{value}}</option>
                </select>
                <span class="toolbar-icon">H</span>
            </div>
        </div>
    `
});