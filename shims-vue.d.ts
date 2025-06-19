declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent&lt;{}, {}, any&gt;
  export default component
}
