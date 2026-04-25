addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
    'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization, X-Requested-With',
  }

  // Handle OPTIONS (preflight)
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: corsHeaders,
    })
  }

  // Forward to Hugging Face Spaces
  const backendUrl = 'https://hilal1-mevzusaglik.hf.space'
  const url = new URL(request.url)
  
  // Preserve the path
  const forwardUrl = `${backendUrl}${url.pathname}${url.search}`

  // Create new headers - TÜM HEADER'LARI FORWARD ET
  const headers = new Headers(request.headers)

  // DEBUG: Log headers
  console.log('=== INCOMING REQUEST ===')
  console.log('URL:', forwardUrl)
  console.log('Method:', request.method)
  console.log('X-API-Key:', headers.get('X-API-Key'))
  console.log('Content-Type:', headers.get('Content-Type'))

  // Prepare request body - ÖNEMLI: stream'i tüketmeden clone et
  let body = null
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    // POST, PUT, DELETE için body'yi forward et
    // Clone request'i kullan ki stream tüketilmesin
    body = await request.clone().arrayBuffer()
    console.log('Body size:', body.byteLength)
  }

  // Forward the request
  const forwardRequest = new Request(forwardUrl, {
    method: request.method,
    headers: headers,
    body: body ? body : undefined,
  })

  try {
    const response = await fetch(forwardRequest)
    
    // DEBUG: Log response
    console.log('=== BACKEND RESPONSE ===')
    console.log('Status:', response.status, response.statusText)

    // Create a new response with CORS headers
    const newResponse = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    })

    // Add CORS headers
    Object.keys(corsHeaders).forEach(key => {
      newResponse.headers.set(key, corsHeaders[key])
    })

    return newResponse
  } catch (error) {
    console.error('=== PROXY ERROR ===')
    console.error('Error:', error)
    return new Response(JSON.stringify({ error: 'Proxy error', message: error.message }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    })
  }
}
