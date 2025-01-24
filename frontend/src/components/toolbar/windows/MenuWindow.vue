<template>
  <div>
    <div class="menu-window">
      <div class="window-label">graph settings</div>
      <div class="menu-items">
        <ConnectedGraph :mode="mode"></ConnectedGraph>
        <ShowModules :mode="mode"></ShowModules>
        <ModuleSelection :mode="mode"></ModuleSelection>
        <EdgeOpacity :mode="mode"></EdgeOpacity>
        <NodeLabelSelect :mode="mode"></NodeLabelSelect>
      </div>
      <div v-if="mode == 'term'">
        <div class="window-label">visualize fdr-rate</div>
        <div class="menu-items">
          <FDRValue></FDRValue>
        </div>
      </div>
      <div class="window-label">export graph</div>
      <div class="menu-items">
        <ExportingButton :mode="mode"></ExportingButton>
        <ExportGraph v-if="mode == 'protein'"></ExportGraph>
        <ExportProteins
          v-if="mode == 'protein'"
          :gephi_data="gephi_data"
        ></ExportProteins>
        <ExportEdges
          v-if="mode == 'protein'"
          :gephi_data="gephi_data"
          :ensembl_name_index="ensembl_name_index"
        ></ExportEdges>
      </div>
    </div>
  </div>
</template>

<script>
import ExportProteins from "@/components/toolbar/modules/ExportProteins.vue";
import ExportEdges from "@/components/toolbar/modules/ExportEdges.vue";
import ExportingButton from "@/components/toolbar/modules/ExportingButton.vue";
import FDRValue from "@/components/toolbar/modules/FDRValue.vue";
import ExportGraph from "@/components/toolbar/modules/ExportGraph.vue";
import NodeLabelSelect from "@/components/toolbar/modules/NodeLabelSelect.vue";
import ConnectedGraph from "@/components/toolbar/modules/ConnectedGraph.vue";
import ShowModules from "@/components/toolbar/modules/ShowModules.vue";
import EdgeOpacity from "@/components/toolbar/modules/EdgeOpacity.vue";
import ModuleSelection from "@/components/toolbar/modules/ModuleSelection.vue";

export default {
  name: "MenuWindow",
  props: ["tools_active", "mode", "gephi_data", "ensembl_name_index"],
  emits: ["tools_active_changed"],
  components: {
    ExportingButton,
    ExportGraph,
    EdgeOpacity,
    NodeLabelSelect,
    ConnectedGraph,
    ModuleSelection,
    FDRValue,
    ExportProteins,
    ExportEdges,
    ShowModules,
  },
  data() {
    return {};
  },
};
</script>

<style>
.menu-window {
  position: absolute;
  height: fit-content;
  width: 22%;
  top: 5vw;
  padding: 0.3% 0 0.3% 0;
  border-radius: 5px;
  background: grey;
  overflow-y: scroll;
  overflow-x: hidden;
  color: white;
  border-top-color: rgba(255, 255, 255, 30%);
  border-top-width: 1px;
  border-top-style: solid;
  cursor: default;
  z-index: 1;
  margin-left: 3vw;
}

/* Hide scrollbar for Chrome, Safari and Opera */
.menu-window::-webkit-scrollbar {
  display: none;
}

.menu-window:after {
  content: "";
  position: absolute;
  z-index: -1;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(7.5px);
}

.menu-items {
  margin: 1% 0 1% 6%;
  width: 100%;
  color: white;
}

.window-label {
  margin-left: 3%;
  width: 93%;
  font-family: "ABeeZee", sans-serif;
  color: rgba(255, 255, 255, 50%);
  font-size: 0.7vw;
  border-bottom: 1px solid;
  border-color: rgba(255, 255, 255, 50%);
  cursor: default;
}

.tool-item {
  font-family: "ABeeZee", sans-serif;
  font-size: 1vw;
  display: flex;
}

.menu-window [type="checkbox"],
.context-check [type="checkbox"] {
  display: none;
  z-index: 0;
}

.menu-window [type="checkbox"] + label,
.context-check [type="checkbox"] + label {
  display: block;
  cursor: pointer;
  font-family: sans-serif;
  font-size: 24px;
  line-height: 1.3;
  position: absolute;
  right: 15%;
  margin-top: 0.7%;
}
.menu-window [type="checkbox"] + label:before,
.context-check [type="checkbox"] + label:before {
  width: 1.8vw;
  height: 0.9vw;
  border-radius: 30px;
  background-color: #ddd;
  content: "";
  transition: background-color 0.5s linear;
  z-index: 5;
  position: absolute;
}
.menu-window [type="checkbox"] + label:after,
.context-check [type="checkbox"] + label:after {
  width: 0.7vw;
  height: 0.7vw;
  border-radius: 30px;
  background-color: #fff;
  content: "";
  transition: margin 0.1s linear;
  box-shadow: 0px 0px 5px #aaa;
  position: absolute;
  top: 10%;
  margin: 0.1vw 0 0 0.1vw;
  z-index: 10;
}
.protein-view [type="checkbox"]:checked + label:before {
  background-color: #0a0a1a;
}
.term-view [type="checkbox"]:checked + label:before {
  background-color: #0a1a0b;
}
.menu-window [type="checkbox"]:checked + label:after {
  margin: 0.1vw 0 0 1vw;
}
</style>
