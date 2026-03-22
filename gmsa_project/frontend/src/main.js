/**
 * Archivo : main.js
 * Descripción:
 *   Punto de entrada principal del frontend Svelte.
 *
 *   Este archivo es el primer módulo que ejecuta el navegador. Su única
 *   responsabilidad es importar los estilos globales y montar el componente
 *   raíz ``App`` en el elemento HTML con id ``app`` definido en ``index.html``.
 *
 * Arquitectura:
 *   Utiliza la API ``mount`` de Svelte 5 para inicializar la aplicación.
 *   A partir de aquí, toda la lógica de la UI queda encapsulada en el
 *   árbol de componentes con raíz en ``App.svelte``.
 */

import './app.css'
import App from './App.svelte'
import { mount } from 'svelte'

// Montar el componente raíz en el contenedor definido en index.html.
mount(App, {
  target: document.getElementById('app')
})
