
<template lang="pug">
  v-layout(row='', wrap='')
    v-flex.text-xs-left(sm8, d-flex)
      v-card.kaapana-opacity-card(width='160%')
        v-card-text.text-xs-left
          v-layout(row='', wrap='')
            v-flex(xs12, py-1)
              div(style={'margin': '9px', 'margin-top': '10px'})
                img(src='../../assets/img/aihealth.png', alt='Vuetify', width='100%')
    v-flex.text-xs-left(sm4 d-flex)
      v-card.kaapana-opacity-card(width='100%')
        v-card-text.text-xs-left
          span.kaapana-headline Contact us
          hr.my-2
          v-layout(row='', wrap='')
            v-flex(xs12, py-1)
              v-icon mdi-slack
              |&nbsp;
              a(href="https://aihcluster.slack.com/archives/C03P03WGJSJ") cc-software
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: 'KaapanaWelcome',
  props: {

  },
  computed: {
    ...mapGetters(["commonData"])
  },
  methods:{
    refreshIFrame: function(event){
      this.$refs.iframe.src = this.$refs.iframe.src
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">

.iframe-window {
  border: none;
}

</style>
