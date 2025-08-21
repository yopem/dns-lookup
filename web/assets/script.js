const API_BASE = "/api/dns"

const recordTypes = {
  A: 1,
  AAAA: 28,
  MX: 15,
  NS: 2,
  CNAME: 5,
  TXT: 16,
  SOA: 6,
}

// Theme management
function initTheme() {
  const savedTheme = localStorage.getItem("theme") || "light"
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
  const theme =
    savedTheme === "auto" ? (prefersDark ? "dark" : "light") : savedTheme

  document.documentElement.setAttribute("data-theme", theme)
  updateThemeToggle(theme)
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme")
  const newTheme = currentTheme === "dark" ? "light" : "dark"

  document.documentElement.setAttribute("data-theme", newTheme)
  localStorage.setItem("theme", newTheme)
  updateThemeToggle(newTheme)
}

function updateThemeToggle(theme) {
  const toggleBtn = document.querySelector(".theme-toggle")
  toggleBtn.textContent = theme === "dark" ? "☀️" : "🌙"
  toggleBtn.title =
    theme === "dark" ? "Switch to Light Theme" : "Switch to Dark Theme"
}

function showAlert(message) {
  const alert = document.createElement("div")
  alert.className = "alert"
  alert.textContent = message
  document.body.appendChild(alert)

  setTimeout(() => {
    alert.remove()
  }, 3000)
}

function validateDomain(domain) {
  const domainRegex =
    /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/
  return domainRegex.test(domain)
}

async function lookupDNS(domain, type) {
  const typeCode = recordTypes[type]
  const url = `${API_BASE}?name=${encodeURIComponent(domain)}&type=${typeCode}`

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return data
  } catch (error) {
    console.error("DNS lookup error:", error)
    return { Status: 2, Answer: [] }
  }
}

function formatRecord(answer, type) {
  if (!answer || !answer.data) return "NO DATA"

  switch (type) {
    case "A":
    case "AAAA":
      return answer.data
    case "MX":
      const parts = answer.data.split(" ")
      return `PRIORITY: ${parts[0]}, SERVER: ${parts.slice(1).join(" ")}`
    case "NS":
    case "CNAME":
      return answer.data.endsWith(".") ? answer.data.slice(0, -1) : answer.data
    case "TXT":
      return answer.data.replace(/"/g, "")
    case "SOA":
      const soaParts = answer.data.split(" ")
      return `PRIMARY NS: ${soaParts[0]}, EMAIL: ${soaParts[1]}, SERIAL: ${soaParts[2]}`
    default:
      return answer.data
  }
}

function displayResults(results, domain) {
  const resultsContent = document.getElementById("resultsContent")
  resultsContent.innerHTML = ""

  let hasResults = false

  for (const [type, data] of Object.entries(results)) {
    if (data.Answer && data.Answer.length > 0) {
      hasResults = true
      const recordDiv = document.createElement("div")
      recordDiv.className = "record-type"

      const title = document.createElement("h3")
      title.textContent = `${type} RECORDS`
      recordDiv.appendChild(title)

      data.Answer.forEach((answer) => {
        const valueDiv = document.createElement("div")
        valueDiv.className = "record-value"
        valueDiv.textContent = formatRecord(answer, type)
        recordDiv.appendChild(valueDiv)
      })

      resultsContent.appendChild(recordDiv)
    } else if (data.Status !== 0) {
      const errorDiv = document.createElement("div")
      errorDiv.className = "error"
      errorDiv.textContent = `${type}: NO RECORDS FOUND`
      resultsContent.appendChild(errorDiv)
    }
  }

  if (!hasResults) {
    const noResultsDiv = document.createElement("div")
    noResultsDiv.className = "no-results"
    noResultsDiv.textContent = `NO DNS RECORDS FOUND FOR ${domain.toUpperCase()}`
    resultsContent.appendChild(noResultsDiv)
  }
}

async function performLookup() {
  const domain = document.getElementById("domain").value.trim()
  const recordType = document.getElementById("recordType").value

  if (!domain) {
    showAlert("PLEASE ENTER A DOMAIN NAME")
    return
  }

  if (!validateDomain(domain)) {
    showAlert("PLEASE ENTER A VALID DOMAIN NAME")
    return
  }

  const results = document.getElementById("results")
  const loading = document.getElementById("loading")
  const resultsContent = document.getElementById("resultsContent")

  results.style.display = "block"
  loading.style.display = "block"
  resultsContent.innerHTML = ""

  try {
    const lookupResults = {}

    if (recordType === "ALL") {
      const promises = Object.keys(recordTypes).map(async (type) => {
        const result = await lookupDNS(domain, type)
        lookupResults[type] = result
      })
      await Promise.all(promises)
    } else {
      const result = await lookupDNS(domain, recordType)
      lookupResults[recordType] = result
    }

    loading.style.display = "none"
    displayResults(lookupResults, domain)
  } catch (error) {
    loading.style.display = "none"
    const errorDiv = document.createElement("div")
    errorDiv.className = "error"
    errorDiv.textContent = `ERROR PERFORMING DNS LOOKUP: ${error.message.toUpperCase()}`
    resultsContent.appendChild(errorDiv)
  }
}

function clearResults() {
  document.getElementById("domain").value = ""
  document.getElementById("recordType").value = "ALL"
  document.getElementById("results").style.display = "none"
}

// Event listeners
document.getElementById("domain").addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    performLookup()
  }
})

// System theme change detection
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", function (e) {
    if (localStorage.getItem("theme") === "auto") {
      const theme = e.matches ? "dark" : "light"
      document.documentElement.setAttribute("data-theme", theme)
      updateThemeToggle(theme)
    }
  })

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  initTheme()

  // Check URL parameters for pre-filling
  const urlParams = new URLSearchParams(window.location.search)
  const domain = urlParams.get("domain")
  const type = urlParams.get("type")

  if (domain) {
    document.getElementById("domain").value = domain
  }

  if (type && type !== "ALL") {
    document.getElementById("recordType").value = type
  }

  // Auto-perform lookup if domain is provided via URL
  if (domain) {
    performLookup()
  } else {
    document.getElementById("domain").focus()
  }
})
