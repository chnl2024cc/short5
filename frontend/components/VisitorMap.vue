<template>
  <div class="visitor-map-container">
    <div id="visitor-map" class="w-full h-96 rounded-lg"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  locations: Array<{
    latitude: number
    longitude: number
    country?: string
    country_name?: string
    city?: string
    visit_count: number
    unique_visitors: number
  }>
}>()

let map: any = null
let markers: any[] = []
let LeafletModule: any = null

onMounted(async () => {
  // Dynamically import Leaflet (client-side only, lazy-loaded)
  // This ensures Leaflet is NOT bundled in the main app bundle
  // Only loaded when admin visits the Visitor Analytics tab
  if (process.client) {
    LeafletModule = await import('leaflet')
    await import('leaflet/dist/leaflet.css')
  
    // Initialize map
    map = LeafletModule.default.map('visitor-map').setView([20, 0], 2)
    
    // Add tile layer (OpenStreetMap)
    LeafletModule.default.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map)
    
    updateMarkers()
  }
})

watch(() => props.locations, () => {
  updateMarkers()
}, { deep: true })

const updateMarkers = async () => {
  if (!map || !LeafletModule) {
    // Ensure Leaflet is loaded
    if (process.client && !LeafletModule) {
      LeafletModule = await import('leaflet')
    }
    if (!LeafletModule) return
  }
  
  // Clear existing markers
  markers.forEach(marker => map.removeLayer(marker))
  markers = []
  
  // Add new markers
  props.locations.forEach(location => {
    const marker = LeafletModule.default.circleMarker(
      [location.latitude, location.longitude],
      {
        radius: Math.min(Math.max(location.visit_count / 10, 5), 30),
        fillColor: '#3b82f6',
        color: '#1e40af',
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.6,
      }
    )
    
    const popupContent = `
      <div class="p-2">
        <div class="font-bold">${location.city || 'Unknown'}, ${location.country_name || location.country || 'Unknown'}</div>
        <div class="text-sm text-gray-600">Visits: ${location.visit_count}</div>
        <div class="text-sm text-gray-600">Unique Visitors: ${location.unique_visitors}</div>
        <div class="text-xs text-gray-500">${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}</div>
      </div>
    `
    
    marker.bindPopup(popupContent)
    marker.addTo(map)
    markers.push(marker)
  })
  
  // Fit map to show all markers
  if (markers.length > 0 && LeafletModule) {
    const group = new LeafletModule.default.FeatureGroup(markers)
    map.fitBounds(group.getBounds().pad(0.1))
  }
}

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.visitor-map-container {
  width: 100%;
  height: 100%;
}

#visitor-map {
  z-index: 0;
}
</style>

