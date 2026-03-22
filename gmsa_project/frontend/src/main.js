import './app.css'
import App from './App.svelte'
import { mount } from 'svelte'

// Punto de entrada del frontend.
mount(App, {
  target: document.getElementById('app')
})
