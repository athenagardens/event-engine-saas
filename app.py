<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Executive Enterprise Venue & Event Operating Platform</title>
  
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0fdf4',
              100: '#dcfce7',
              500: '#22c55e',
              600: '#16a34a',
              800: '#166534',
              900: '#14532d',
            },
            exec: {
              dark: '#0f172a',
              slate: '#1e293b',
              gold: '#d97706',
              goldHover: '#b45309',
              bg: '#f8fafc',
            }
          },
          fontFamily: {
            serif: ['Playfair Display', 'Georgia', 'serif'],
            sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
          }
        }
      }
    }
  </script>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">

  <!-- FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

  <!-- QR Code Generator Library -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
  
  <!-- jsPDF Library for Client-side PDF Generation -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

  <style>
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #f8fafc;
      color: #0f172a;
    }
    .font-serif-title {
      font-family: 'Playfair Display', Georgia, serif;
    }
    .gold-divider {
      height: 2px;
      background: linear-gradient(90deg, transparent, #d97706, transparent);
      margin: 0.5rem auto 1.5rem auto;
      width: 50%;
    }
    .ticket-pass {
      background: #ffffff;
      border: 2px dashed #0f172a;
    }
    /* Printable ticket styles */
    @media print {
      body * {
        visibility: hidden;
      }
      #printable-area, #printable-area * {
        visibility: visible;
      }
      #printable-area {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
      }
      .no-print {
        display: none !important;
      }
    }
  </style>
</head>
<body class="bg-slate-50 min-h-screen flex flex-col md:flex-row">

  <!-- SIDEBAR NAVIGATION -->
  <aside class="w-full md:w-80 bg-slate-900 text-white flex-shrink-0 min-h-screen flex flex-col justify-between border-r border-slate-800 no-print">
    <div>
      <!-- Header -->
      <div class="p-6 text-center border-b border-slate-800">
        <h2 class="text-2xl font-bold font-serif-title text-amber-500 tracking-wide flex items-center justify-center gap-2">
          <span>🏛️</span> EXECUTIVE PORTAL
        </h2>
        <p class="text-xs uppercase tracking-widest text-slate-400 font-semibold mt-1">Enterprise SaaS Infrastructure</p>
      </div>

      <!-- Navigation Radio-Style Menu -->
      <nav class="p-4 space-y-2" id="nav-menu">
        <button onclick="switchTab('tab-marketplace')" id="btn-tab-marketplace" class="nav-btn w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-sm font-medium transition-all bg-amber-600 text-white shadow">
          <i class="fa-solid fa-[#0073e6] fa-store text-lg w-6"></i>
          <span>Enterprise Marketplace & Event Hub</span>
        </button>

        <button onclick="switchTab('tab-venue-ops')" id="btn-tab-venue-ops" class="nav-btn w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white">
          <i class="fa-solid fa-building text-lg w-6"></i>
          <span>Venue Operations & Analytics</span>
        </button>

        <button onclick="switchTab('tab-vendor')" id="btn-tab-vendor" class="nav-btn w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white">
          <i class="fa-solid fa-truck-ramp-box text-lg w-6"></i>
          <span>Vendor Portal & Service Fulfillment</span>
        </button>

        <button onclick="switchTab('tab-access')" id="btn-tab-access" class="nav-btn w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white">
          <i class="fa-solid fa-qrcode text-lg w-6"></i>
          <span>Access Control & Verification Suite</span>
        </button>

        <button onclick="switchTab('tab-ledger')" id="btn-tab-ledger" class="nav-btn w-full text-left px-4 py-3 rounded-lg flex items-center gap-3 text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white">
          <i class="fa-solid fa-file-invoice-dollar text-lg w-6"></i>
          <span>Executive Master Ledger & Audit Suite</span>
        </button>
      </nav>
    </div>

    <!-- Auth & Maintenance Footer -->
    <div class="p-4 border-t border-slate-800 space-y-3">
      <div id="auth-status" class="bg-slate-800/80 p-3 rounded border border-slate-700 text-xs text-slate-300">
        <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1.5"></span>
        Status: <strong class="text-white">Public / Guest Session</strong>
      </div>

      <button onclick="resetDatabaseState()" class="w-full bg-rose-900/40 hover:bg-rose-800 text-rose-200 border border-rose-700 text-xs py-2 px-3 rounded transition flex items-center justify-center gap-2 font-semibold">
        <i class="fa-solid fa-rotate-right"></i> Reset Database State
      </button>
    </div>
  </aside>

  <!-- MAIN CONTENT AREA -->
  <main class="flex-grow p-4 md:p-8 overflow-y-auto">

    <!-- ========================================================= -->
    <!-- MODULE 1: ENTERPRISE MARKETPLACE & EVENT HUB -->
    <!-- ========================================================= -->
    <section id="tab-marketplace" class="tab-content">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold font-serif-title text-slate-900">Enterprise Marketplace & Event Hub</h1>
        <p class="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Commercial Venue Reservations & Public Event Ticketing</p>
        <div class="gold-divider"></div>
      </div>

      <!-- Inner Tabs -->
      <div class="flex border-b border-slate-200 mb-6 bg-white rounded-t-lg p-1 shadow-sm max-w-3xl mx-auto">
        <button onclick="switchSubTab('mkt-reservations')" id="btn-mkt-reservations" class="subtab-btn flex-1 py-2.5 px-4 text-center text-sm font-semibold rounded-md bg-slate-900 text-white transition">
          🏛️ Commercial Venue Reservations
        </button>
        <button onclick="switchSubTab('mkt-tickets')" id="btn-mkt-tickets" class="subtab-btn flex-1 py-2.5 px-4 text-center text-sm font-semibold rounded-md text-slate-600 hover:text-slate-900 transition">
          🎟️ Box Office Event Tickets
        </button>
        <button onclick="switchSubTab('mkt-passes')" id="btn-mkt-passes" class="subtab-btn flex-1 py-2.5 px-4 text-center text-sm font-semibold rounded-md text-slate-600 hover:text-slate-900 transition">
          🎫 My Issued Ticket Passes
        </button>
      </div>

      <!-- SUBTAB 1: VENUE RESERVATIONS -->
      <div id="mkt-reservations" class="subtab-content">
        <div class="max-w-4xl mx-auto bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
          
          <!-- Step 1: Select Venue -->
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">1. Select Destination Venue Facility</label>
            <select id="res-venue-select" onchange="renderVenueDetails()" class="w-full bg-slate-50 border border-slate-300 rounded p-3 text-slate-800 focus:ring-2 focus:ring-amber-500 font-medium">
              <!-- Dynamic Venues -->
            </select>
          </div>

          <!-- Venue Banner Card -->
          <div id="venue-banner-card" class="bg-slate-900 text-white rounded-lg p-5 flex flex-col md:flex-row gap-6 items-center border-t-4 border-amber-500">
            <!-- Dynamic Content -->
          </div>

          <hr class="border-slate-200">

          <!-- Step 2: Space & Date Selection -->
          <h3 class="text-lg font-serif-title font-bold text-center text-slate-800">2. Space Selection & Event Scheduling</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Sub-Space Asset</label>
              <select id="res-space-select" onchange="calculateReservationCost()" class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-slate-800 text-sm">
                <!-- Dynamic Spaces -->
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Event Date</label>
              <input type="date" id="res-date-input" onchange="checkAvailability()" class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-slate-800 text-sm font-medium">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Duration (Days)</label>
              <input type="number" id="res-days-input" min="1" value="1" onchange="calculateReservationCost()" class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-slate-800 text-sm">
            </div>
          </div>

          <div id="availability-status" class="p-3 rounded text-sm text-center font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
            ✅ Schedule Confirmed: Available for booking.
          </div>

          <hr class="border-slate-200">

          <!-- Step 3: Ancillary Vendors -->
          <h3 class="text-lg font-serif-title font-bold text-center text-slate-800">3. Ancillary Vendor Service Bundles</h3>
          <div id="vendor-services-accordion" class="space-y-3">
            <!-- Dynamic Vendor Packages -->
          </div>

          <hr class="border-slate-200">

          <!-- Step 4: Settlement & Contact Info -->
          <h3 class="text-lg font-serif-title font-bold text-center text-slate-800">4. Settlement & Billing Confirmation</h3>
          <form id="reservation-form" onsubmit="handleReservationSubmit(event)" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Client Entity / Full Name *</label>
                <input type="text" id="res-client-name" required class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-sm" placeholder="e.g. Apex Corporation">
              </div>
              <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Contact Phone / WhatsApp Line *</label>
                <input type="tel" id="res-client-phone" required class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-sm" placeholder="+267 71 234 567">
              </div>
              <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Billing Email Address *</label>
                <input type="email" id="res-client-email" required class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-sm" placeholder="billing@apex.co.bw">
              </div>
              <div>
                <label class="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">Preferred Settlement Method</label>
                <select id="res-payment-method" class="w-full bg-slate-50 border border-slate-300 rounded p-2.5 text-sm">
                  <option value="Direct Bank Wire Transfer">Direct Bank Wire Transfer</option>
                  <option value="eWallet">eWallet</option>
                  <option value="Orange Money">Orange Money</option>
                  <option value="Pay2Cell">Pay2Cell</option>
                </select>
              </div>
            </div>

            <!-- Cost Summary Box -->
            <div class="bg-slate-100 p-4 rounded border border-slate-300 flex justify-between items-center font-bold text-slate-900">
              <span>ESTIMATED TOTAL DUE:</span>
              <span id="res-total-display" class="text-xl text-amber-600">BWP 0.00</span>
            </div>

            <button type="submit" class="w-full bg-slate-900 hover:bg-amber-600 text-white font-semibold py-3 px-6 rounded transition shadow-md uppercase tracking-wider text-sm">
              Submit Reservation & Generate Invoices
            </button>
          </form>

          <!-- Generated Downloads Container -->
          <div id="reservation-downloads" class="hidden p-4 bg-emerald-50 border border-emerald-200 rounded space-y-3">
            <h4 class="font-bold text-emerald-900 flex items-center gap-2">
              <i class="fa-solid fa-circle-check text-emerald-600"></i> Reservation Successfully Issued!
            </h4>
            <p class="text-xs text-emerald-700">Download your official tax PDF invoices below:</p>
            <div id="download-buttons-list" class="flex flex-wrap gap-2"></div>
          </div>

        </div>
      </div>

      <!-- SUBTAB 2: BOX OFFICE EVENT TICKETS -->
      <div id="mkt-tickets" class="subtab-content hidden">
        <div class="max-w-4xl mx-auto space-y-6" id="public-events-list">
          <!-- Dynamic Public Events List -->
        </div>
      </div>

      <!-- SUBTAB 3: VIEW MY ISSUED PASSES -->
      <div id="mkt-passes" class="subtab-content hidden">
        <div class="max-w-xl mx-auto bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-lg font-serif-title font-bold text-slate-900 text-center">Lookup Issued Admission Passes</h3>
          <div class="flex gap-2">
            <input type="email" id="pass-lookup-email" placeholder="Enter your registered email address..." class="flex-grow bg-slate-50 border border-slate-300 rounded p-2.5 text-sm">
            <button onclick="lookupPasses()" class="bg-slate-900 hover:bg-amber-600 text-white px-5 py-2.5 rounded font-semibold text-sm transition">
              Search
            </button>
          </div>
          <div id="issued-passes-result" class="space-y-4 mt-6"></div>
        </div>
      </div>

    </section>

    <!-- ========================================================= -->
    <!-- MODULE 2: VENUE OPERATIONS & ANALYTICS -->
    <!-- ========================================================= -->
    <section id="tab-venue-ops" class="tab-content hidden">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold font-serif-title text-slate-900">Venue Operations & Console</h1>
        <p class="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Property Settings, Space Allocation & Financial Analytics</p>
        <div class="gold-divider"></div>
      </div>

      <div class="max-w-5xl mx-auto space-y-8">
        
        <!-- Metrics Bar -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-white p-4 rounded border border-slate-200 border-l-4 border-l-amber-500 text-center shadow-sm">
            <p class="text-xs font-bold uppercase text-slate-500">Total Bookings</p>
            <p id="metric-bookings-count" class="text-2xl font-bold text-slate-900 mt-1">0</p>
          </div>
          <div class="bg-white p-4 rounded border border-slate-200 border-l-4 border-l-emerald-500 text-center shadow-sm">
            <p class="text-xs font-bold uppercase text-slate-500">Gross Hire Revenue</p>
            <p id="metric-venue-revenue" class="text-2xl font-bold text-slate-900 mt-1">BWP 0.00</p>
          </div>
          <div class="bg-white p-4 rounded border border-slate-200 border-l-4 border-l-blue-500 text-center shadow-sm">
            <p class="text-xs font-bold uppercase text-slate-500">Active Spaces</p>
            <p id="metric-spaces-count" class="text-2xl font-bold text-slate-900 mt-1">0</p>
          </div>
        </div>

        <!-- Venue Management Forms -->
        <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
          <h3 class="text-xl font-serif-title font-bold text-slate-900 border-b pb-2">Facility Branding & Configuration</h3>
          <form onsubmit="saveVenueSettings(event)" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Venue Business Name</label>
              <input type="text" id="ops-venue-name" required class="w-full bg-slate-50 border rounded p-2 text-sm">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Max Licensed Capacity</label>
              <input type="number" id="ops-venue-capacity" required class="w-full bg-slate-50 border rounded p-2 text-sm">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">WhatsApp Line</label>
              <input type="text" id="ops-venue-whatsapp" required class="w-full bg-slate-50 border rounded p-2 text-sm">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Tax / CIPA Registration ID</label>
              <input type="text" id="ops-venue-tax" required class="w-full bg-slate-50 border rounded p-2 text-sm">
            </div>
            <div class="md:col-span-2">
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Bank Settlement Details</label>
              <textarea id="ops-venue-bank" rows="2" class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="Bank Name, Account Number, Branch Code..."></textarea>
            </div>
            <button type="submit" class="md:col-span-2 bg-slate-900 hover:bg-amber-600 text-white font-semibold py-2.5 rounded transition text-sm uppercase">
              Save Facility Profile
            </button>
          </form>
        </div>

        <!-- Create Event Flyer Module -->
        <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-xl font-serif-title font-bold text-slate-900 border-b pb-2">Publish Public Box Office Event</h3>
          <form onsubmit="publishPublicEvent(event)" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Event Title</label>
              <input type="text" id="ops-event-title" required class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="e.g. Summer Executive Gala">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Event Date</label>
              <input type="date" id="ops-event-date" required class="w-full bg-slate-50 border rounded p-2 text-sm">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Admission Price (BWP)</label>
              <input type="number" step="0.01" id="ops-event-price" required class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="250.00">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Flyer Image URL</label>
              <input type="url" id="ops-event-flyer" class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="https://images.unsplash.com/...">
            </div>
            <div class="md:col-span-2">
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Event Description & Lineup</label>
              <textarea id="ops-event-desc" rows="2" class="w-full bg-slate-50 border rounded p-2 text-sm"></textarea>
            </div>
            <button type="submit" class="md:col-span-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2.5 rounded transition text-sm uppercase">
              Publish Event to Public Hub
            </button>
          </form>
        </div>

      </div>
    </section>

    <!-- ========================================================= -->
    <!-- MODULE 3: VENDOR PORTAL & SERVICE FULFILLMENT -->
    <!-- ========================================================= -->
    <section id="tab-vendor" class="tab-content hidden">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold font-serif-title text-slate-900">Vendor Portal & Fulfillment</h1>
        <p class="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Ancillary Service Catalog & Invoicing Management</p>
        <div class="gold-divider"></div>
      </div>

      <div class="max-w-5xl mx-auto space-y-6">
        <!-- Vendor Catalog Form -->
        <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-xl font-serif-title font-bold text-slate-900 border-b pb-2">Add Service Offering to Catalog</h3>
          <form onsubmit="addVendorItem(event)" class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Service / Package Item</label>
              <input type="text" id="vnd-item-name" required class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="e.g. VIP Catering Setup">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Unit Tariff Price (BWP)</label>
              <input type="number" step="0.01" id="vnd-item-price" required class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="1500.00">
            </div>
            <div>
              <label class="block text-xs font-bold uppercase text-slate-700 mb-1">Unit Basis</label>
              <input type="text" id="vnd-item-unit" required class="w-full bg-slate-50 border rounded p-2 text-sm" placeholder="e.g. Per Guest / Day">
            </div>
            <div class="md:col-span-3">
              <button type="submit" class="w-full bg-slate-900 hover:bg-amber-600 text-white font-semibold py-2.5 rounded transition text-sm uppercase">
                Add Package to Active Catalog
              </button>
            </div>
          </form>
        </div>

        <!-- Vendor Orders Table -->
        <div class="bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 class="text-xl font-serif-title font-bold text-slate-900 border-b pb-2">Assigned Service Orders</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-left text-sm text-slate-700 border-collapse">
              <thead>
                <tr class="bg-slate-900 text-white text-xs uppercase">
                  <th class="p-3">Invoice Ref</th>
                  <th class="p-3">Venue Facility</th>
                  <th class="p-3">Client Contact</th>
                  <th class="p-3">Event Date</th>
                  <th class="p-3">Total Amount</th>
                  <th class="p-3">Status</th>
                </tr>
              </thead>
              <tbody id="vendor-orders-table-body" class="divide-y divide-slate-200">
                <!-- Dynamic Vendor Invoices -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- ========================================================= -->
    <!-- MODULE 4: ACCESS CONTROL & VERIFICATION SUITE -->
    <!-- ========================================================= -->
    <section id="tab-access" class="tab-content hidden">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold font-serif-title text-slate-900">Access Control & Verification Suite</h1>
        <p class="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Real-Time Ticket Scanning & Entry Audit</p>
        <div class="gold-divider"></div>
      </div>

      <div class="max-w-xl mx-auto bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
        <div class="text-center">
          <i class="fa-solid fa-qrcode text-5xl text-slate-800 mb-2"></i>
          <h3 class="text-lg font-serif-title font-bold text-slate-900">Scan & Validate Admission Pass</h3>
          <p class="text-xs text-slate-500">Enter ticket pass code or verification hash manually to process entry.</p>
        </div>

        <div class="space-y-3">
          <input type="text" id="scan-ticket-id" placeholder="Paste Ticket Pass Hash or Ref (e.g. TKT-1690000000)..." class="w-full bg-slate-50 border border-slate-300 rounded p-3 text-center text-slate-800 font-mono text-sm">
          <button onclick="verifyTicketPass()" class="w-full bg-slate-900 hover:bg-emerald-600 text-white font-semibold py-3 rounded transition uppercase text-sm">
            Verify Ticket Code
          </button>
        </div>

        <!-- Verification Results Box -->
        <div id="scan-result-card" class="hidden p-4 rounded border text-center space-y-2">
          <!-- Dynamic Scanner Response -->
        </div>
      </div>
    </section>

    <!-- ========================================================= -->
    <!-- MODULE 5: EXECUTIVE MASTER LEDGER & AUDIT SUITE -->
    <!-- ========================================================= -->
    <section id="tab-ledger" class="tab-content hidden">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold font-serif-title text-slate-900">Executive Master Ledger & Audit Suite</h1>
        <p class="text-xs uppercase tracking-widest text-slate-500 font-semibold mt-1">Cross-Platform Audit Trail & Financial Settlement Verification</p>
        <div class="gold-divider"></div>
      </div>

      <div class="max-w-6xl mx-auto bg-white p-6 rounded-lg border border-slate-200 shadow-sm space-y-6">
        <h3 class="text-xl font-serif-title font-bold text-slate-900 border-b pb-2">Master Venue Bookings Ledger</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-slate-700 border-collapse">
            <thead>
              <tr class="bg-slate-900 text-white text-xs uppercase">
                <th class="p-3">Booking ID</th>
                <th class="p-3">Client Entity</th>
                <th class="p-3">Space Hired</th>
                <th class="p-3">Event Date</th>
                <th class="p-3">Total Cost</th>
                <th class="p-3">Status</th>
                <th class="p-3">Action</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body" class="divide-y divide-slate-200">
              <!-- Dynamic Ledger Rows -->
            </tbody>
          </table>
        </div>
      </div>
    </section>

  </main>

  <!-- PRINTABLE TICKET PASS MODAL -->
  <div id="ticket-modal" class="fixed inset-0 bg-slate-900/70 backdrop-blur-sm z-50 flex items-center justify-center hidden p-4">
    <div class="bg-white rounded-lg max-w-md w-full p-6 space-y-4 shadow-2xl relative">
      <button onclick="closeTicketModal()" class="absolute top-3 right-3 text-slate-400 hover:text-slate-800 text-xl font-bold no-print">&times;</button>
      
      <div id="printable-area" class="ticket-pass p-5 rounded border-2 border-dashed border-slate-900 text-center space-y-3">
        <h2 id="modal-event-title" class="text-xl font-bold font-serif-title text-amber-600">EVENT TITLE</h2>
        <p id="modal-venue-name" class="text-xs font-semibold uppercase text-slate-600">VENUE NAME</p>
        <hr class="border-slate-200">
        <div class="text-xs text-slate-700 space-y-1 text-left">
          <p><strong>ATTENDEE:</strong> <span id="modal-buyer-name">John Doe</span></p>
          <p><strong>DATE:</strong> <span id="modal-event-date">2026-10-15</span></p>
          <p><strong>PASS QTY:</strong> <span id="modal-pass-qty">1 Pass</span></p>
          <p><strong>TICKET ID:</strong> <span id="modal-ticket-id" class="font-mono text-slate-500">TKT-000</span></p>
        </div>
        
        <!-- QR Code Container -->
        <div class="flex justify-center py-2">
          <div id="qrcode-container" class="p-2 bg-white border border-slate-300 rounded"></div>
        </div>

        <p class="text-[10px] uppercase text-slate-400">Official Admission Pass — Scan Code at Entry</p>
      </div>

      <button onclick="window.print()" class="w-full bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2.5 rounded transition text-sm uppercase no-print">
        <i class="fa-solid fa-print"></i> Print Ticket Pass
      </button>
    </div>
  </div>

  <!-- JavaScript App Engine -->
  <script>
    // ---------------------------------------------------------
    // 1. IN-MEMORY ENTERPRISE STATE & DATA SEEDING
    // ---------------------------------------------------------
    const DEFAULT_LOGO = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150";
    const SPACE_PRESETS = ["https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400"];

    let appData = {
      venues: [
        {
          venue_id: "VEN-001",
          name: "Grand Horizon Convention Center",
          whatsapp_no: "+267 71 000 111",
          address: "Plot 54321, Financial District, Gaborone",
          max_capacity: 2500,
          tax_id: "CIPA-BW-2026-99",
          bank_details: "First National Bank Botswana | Account: 62000000001 | Branch: 280167",
          brand_color: "#0f172a",
          logo_url: DEFAULT_LOGO,
          flyer_image_url: SPACE_PRESETS[0]
        }
      ],
      spaces: [
        { space_id: 1, venue_id: "VEN-001", name: "Grand Executive Ballroom", capacity: 1200, daily_rate: 15000.00 },
        { space_id: 2, venue_id: "VEN-001", name: "Auditorium Hall A", capacity: 500, daily_rate: 7500.00 }
      ],
      supporters: [
        { supporter_id: "SUP-001", business_name: "Aura Gourmet Catering", category: "Hospitality & Catering", bank_details: "Absa Bank Botswana | Acc: 1234567" }
      ],
      vendor_templates: [
        { template_id: 1, supporter_id: "SUP-001", item_name: "VIP Buffet Banquet Service", description: "3-Course Executive Lunch/Dinner Buffet with service staff.", unit_type: "Guest", unit_price: 350.00 }
      ],
      bookings: [],
      vendor_invoices: [],
      tickets: [],
      events: [
        {
          event_id: "EVT-101",
          venue_id: "VEN-001",
          venue_name: "Grand Horizon Convention Center",
          title: "African Executive Tech & Financial Summit 2026",
          date: "2026-11-20",
          price: 1250.00,
          description: "Premier gathering of leaders across technology, finance, and enterprise real estate.",
          flyer_url: "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=500"
        }
      ]
    };

    // Load from localStorage if available
    function loadStorage() {
      const saved = localStorage.getItem("enterprise_platform_db");
      if (saved) {
        try { appData = JSON.parse(saved); } catch(e) { console.error("Data parse error", e); }
      } else {
        saveStorage();
      }
    }

    function saveStorage() {
      localStorage.setItem("enterprise_platform_db", JSON.stringify(appData));
    }

    function resetDatabaseState() {
      if (confirm("Reset all stored platform state to enterprise default?")) {
        localStorage.removeItem("enterprise_platform_db");
        location.reload();
      }
    }

    // ---------------------------------------------------------
    // 2. TAB NAVIGATION
    // ---------------------------------------------------------
    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
      document.getElementById(tabId).classList.remove('hidden');

      document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('bg-amber-600', 'text-white', 'shadow');
        btn.classList.add('text-slate-300');
      });

      const activeBtn = document.getElementById('btn-' + tabId);
      if (activeBtn) {
        activeBtn.classList.add('bg-amber-600', 'text-white', 'shadow');
        activeBtn.classList.remove('text-slate-300');
      }

      // Refresh section-specific UI
      if (tabId === 'tab-venue-ops') renderVenueOpsUI();
      if (tabId === 'tab-vendor') renderVendorUI();
      if (tabId === 'tab-ledger') renderLedgerUI();
    }

    function switchSubTab(subId) {
      document.querySelectorAll('.subtab-content').forEach(el => el.classList.add('hidden'));
      document.getElementById(subId).classList.remove('hidden');

      document.querySelectorAll('.subtab-btn').forEach(btn => {
        btn.classList.remove('bg-slate-900', 'text-white');
        btn.classList.add('text-slate-600');
      });

      const activeBtn = document.getElementById('btn-' + subId);
      if (activeBtn) {
        activeBtn.classList.add('bg-slate-900', 'text-white');
        activeBtn.classList.remove('text-slate-600');
      }
    }

    // ---------------------------------------------------------
    // 3. MODULE 1: MARKETPLACE & RESERVATIONS
    // ---------------------------------------------------------
    function initMarketplaceUI() {
      const vSelect = document.getElementById('res-venue-select');
      vSelect.innerHTML = appData.venues.map(v => `<option value="${v.venue_id}">${v.name}</option>`).join('');
      
      // Default Date to Tomorrow
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      document.getElementById('res-date-input').value = tomorrow.toISOString().split('T')[0];

      renderVenueDetails();
      renderPublicEvents();
    }

    function renderVenueDetails() {
      const vId = document.getElementById('res-venue-select').value;
      const venue = appData.venues.find(v => v.venue_id === vId);
      if (!venue) return;

      // Banner Card
      document.getElementById('venue-banner-card').style.borderTopColor = venue.brand_color || '#d97706';
      document.getElementById('venue-banner-card').innerHTML = `
        <div class="flex-grow">
          <h2 class="text-2xl font-bold font-serif-title">${venue.name}</h2>
          <p class="text-xs text-slate-300 mt-1"><i class="fa-solid fa-location-dot text-amber-500 mr-1"></i> ${venue.address}</p>
          <div class="mt-3 text-xs space-y-1">
            <p><strong>Max Capacity:</strong> ${venue.max_capacity.toLocaleString()} Guests</p>
            <p><strong>WhatsApp Support:</strong> ${venue.whatsapp_no}</p>
          </div>
        </div>
        <img src="${venue.logo_url}" class="w-20 h-20 object-cover rounded bg-white p-1 border border-slate-700">
      `;

      // Sub-Spaces
      const sSelect = document.getElementById('res-space-select');
      const venueSpaces = appData.spaces.filter(s => s.venue_id === vId);
      sSelect.innerHTML = venueSpaces.map(s => `<option value="${s.name}">${s.name} (Cap: ${s.capacity} | BWP ${s.daily_rate.toLocaleString()}/day)</option>`).join('');

      renderVendorAccordion();
      calculateReservationCost();
      checkAvailability();
    }

    function renderVendorAccordion() {
      const container = document.getElementById('vendor-services-accordion');
      if (appData.supporters.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-500 italic text-center">No ancillary vendor packages currently listed.</p>`;
        return;
      }

      container.innerHTML = appData.supporters.map(sup => {
        const templates = appData.vendor_templates.filter(t => t.supporter_id === sup.supporter_id);
        if (templates.length === 0) return '';

        return `
          <div class="border border-slate-200 rounded overflow-hidden">
            <div class="bg-slate-100 p-3 font-semibold text-xs text-slate-800 uppercase flex justify-between items-center">
              <span>${sup.business_name} (${sup.category})</span>
            </div>
            <div class="p-3 space-y-3 bg-white">
              ${templates.map(t => `
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 border-b border-slate-100 pb-2">
                  <div>
                    <strong class="text-sm text-slate-900">${t.item_name}</strong>
                    <p class="text-xs text-slate-500">${t.description}</p>
                    <p class="text-xs text-amber-600 font-bold mt-0.5">BWP ${t.unit_price.toLocaleString()} per${t.unit_type}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <label class="text-xs text-slate-600 font-bold">Qty:</label>
                    <input type="number" min="0" value="0" data-sup="${sup.supporter_id}" data-price="${t.unit_price}" data-name="${t.item_name}" onchange="calculateReservationCost()" class="vendor-qty-input w-20 bg-slate-50 border rounded p-1 text-sm text-center">
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('');
    }

    function checkAvailability() {
      const vId = document.getElementById('res-venue-select').value;
      const spaceName = document.getElementById('res-space-select').value;
      const date = document.getElementById('res-date-input').value;

      const existing = appData.bookings.find(b => b.venue_id === vId && b.space_name === spaceName && b.booking_date === date && b.status !== 'Cancelled');
      const statusEl = document.getElementById('availability-status');

      if (existing) {
        statusEl.className = "p-3 rounded text-sm text-center font-medium bg-rose-50 text-rose-800 border border-rose-200";
        statusEl.innerHTML = `❌ Date Locked: '${spaceName}' is already reserved on ${date}.`;
      } else {
        statusEl.className = "p-3 rounded text-sm text-center font-medium bg-emerald-50 text-emerald-800 border border-emerald-200";
        statusEl.innerHTML = `✅ Schedule Confirmed: '${spaceName}' is available on ${date}.`;
      }
    }

    function calculateReservationCost() {
      const vId = document.getElementById('res-venue-select').value;
      const spaceName = document.getElementById('res-space-select').value;
      const days = parseInt(document.getElementById('res-days-input').value) || 1;

      const space = appData.spaces.find(s => s.venue_id === vId && s.name === spaceName);
      let total = space ? space.daily_rate * days : 0;

      // Add selected vendor services
      document.querySelectorAll('.vendor-qty-input').forEach(input => {
        const qty = parseInt(input.value) || 0;
        const price = parseFloat(input.dataset.price) || 0;
        total += qty * price;
      });

      document.getElementById('res-total-display').innerText = `BWP ${total.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    }

    function handleReservationSubmit(e) {
      e.preventDefault();
      const vId = document.getElementById('res-venue-select').value;
      const venue = appData.venues.find(v => v.venue_id === vId);
      const spaceName = document.getElementById('res-space-select').value;
      const date = document.getElementById('res-date-input').value;
      const days = parseInt(document.getElementById('res-days-input').value) || 1;
      
      const clientName = document.getElementById('res-client-name').value;
      const clientPhone = document.getElementById('res-client-phone').value;
      const clientEmail = document.getElementById('res-client-email').value;
      const payMethod = document.getElementById('res-payment-method').value;

      const bookingId = "BK-" + Date.now();
      const space = appData.spaces.find(s => s.venue_id === vId && s.name === spaceName);
      const venueCost = space ? space.daily_rate * days : 0;

      const newBooking = {
        booking_id: bookingId,
        venue_id: vId,
        space_name: spaceName,
        customer_name: clientName,
        customer_email: clientEmail,
        customer_phone: clientPhone,
        booking_date: date,
        days: days,
        venue_cost: venueCost,
        payment_method: payMethod,
        status: "Pending POP",
        created_at: new Date().toISOString().split('T')[0]
      };

      appData.bookings.push(newBooking);
      saveStorage();

      // Show Downloads
      const downloadContainer = document.getElementById('reservation-downloads');
      const buttonsList = document.getElementById('download-buttons-list');
      downloadContainer.classList.remove('hidden');

      buttonsList.innerHTML = `
        <button onclick="downloadVenuePDF('${bookingId}')" class="bg-slate-900 hover:bg-slate-800 text-white text-xs px-3 py-2 rounded flex items-center gap-1.5 font-medium transition">
          <i class="fa-solid fa-file-pdf text-amber-500"></i> Venue Hire Tax Invoice PDF
        </button>
      `;

      alert(`Reservation Request #${bookingId} successfully recorded!`);
    }

    // ---------------------------------------------------------
    // 4. PUBLIC EVENTS & TICKETING
    // ---------------------------------------------------------
    function renderPublicEvents() {
      const container = document.getElementById('public-events-list');
      if (appData.events.length === 0) {
        container.innerHTML = `<p class="text-slate-500 text-center py-8">No public events currently scheduled.</p>`;
        return;
      }

      container.innerHTML = appData.events.map(ev => `
        <div class="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm flex flex-col md:flex-row">
          <img src="${ev.flyer_url || SPACE_PRESETS[0]}" class="w-full md:w-56 h-48 md:h-auto object-cover">
          <div class="p-5 flex-grow space-y-3">
            <h3 class="text-xl font-bold font-serif-title text-slate-900">${ev.title}</h3>
            <p class="text-xs text-slate-500">${ev.description}</p>
            <div class="text-xs text-slate-700 font-semibold space-y-1">
              <p><i class="fa-solid fa-building text-amber-600 mr-1"></i> ${ev.venue_name}</p>
              <p><i class="fa-solid fa-calendar text-amber-600 mr-1"></i> Date: ${ev.date}</p>
              <p><i class="fa-solid fa-tag text-amber-600 mr-1"></i> Tariff: BWP ${ev.price.toLocaleString()} per pass</p>
            </div>
            
            <form onsubmit="purchaseTicket(event, '${ev.event_id}')" class="pt-2 border-t border-slate-100 flex flex-wrap gap-2 items-center">
              <input type="text" id="tkt-buyer-${ev.event_id}" placeholder="Your Full Name" required class="bg-slate-50 border rounded p-2 text-xs flex-grow">
              <input type="email" id="tkt-email-${ev.event_id}" placeholder="Your Email Address" required class="bg-slate-50 border rounded p-2 text-xs flex-grow">
              <input type="number" id="tkt-qty-${ev.event_id}" value="1" min="1" required class="bg-slate-50 border rounded p-2 text-xs w-16 text-center">
              <button type="submit" class="bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs px-4 py-2 rounded transition uppercase">
                Purchase Pass
              </button>
            </form>
          </div>
        </div>
      `).join('');
    }

    function purchaseTicket(e, eventId) {
      e.preventDefault();
      const eventObj = appData.events.find(ev => ev.event_id === eventId);
      const buyer = document.getElementById(`tkt-buyer-${eventId}`).value;
      const email = document.getElementById(`tkt-email-${eventId}`).value;
      const qty = parseInt(document.getElementById(`tkt-qty-${eventId}`).value) || 1;

      const ticketId = "TKT-" + Date.now();
      const hash = "HASH-" + Math.random().toString(36).substring(2, 10).toUpperCase();

      const ticket = {
        ticket_id: ticketId,
        verification_hash: hash,
        event_id: eventId,
        event_title: eventObj.title,
        venue_id: eventObj.venue_id,
        venue_name: eventObj.venue_name,
        buyer: buyer,
        email: email,
        qty: qty,
        total_paid: qty * eventObj.price,
        status: "Valid Pass",
        created_at: new Date().toISOString()
      };

      appData.tickets.push(ticket);
      saveStorage();

      openTicketModal(ticket);
    }

    function lookupPasses() {
      const email = document.getElementById('pass-lookup-email').value.trim();
      const resultsContainer = document.getElementById('issued-passes-result');

      const found = appData.tickets.filter(t => t.email.toLowerCase() === email.toLowerCase());
      if (found.length === 0) {
        resultsContainer.innerHTML = `<p class="text-xs text-rose-600 text-center font-semibold">No admission passes found for this email.</p>`;
        return;
      }

      resultsContainer.innerHTML = found.map(t => `
        <div class="border border-slate-200 rounded p-4 bg-slate-50 flex justify-between items-center">
          <div>
            <strong class="text-sm text-slate-900 block">${t.event_title}</strong>
            <span class="text-xs text-slate-500">ID: ${t.ticket_id} | Qty: ${t.qty}</span>
          </div>
          <button onclick='openTicketModal(${JSON.stringify(t)})' class="bg-slate-900 text-white text-xs px-3 py-1.5 rounded hover:bg-amber-600 transition">
            View Ticket Pass
          </button>
        </div>
      `).join('');
    }

    function openTicketModal(ticket) {
      document.getElementById('modal-event-title').innerText = ticket.event_title;
      document.getElementById('modal-venue-name').innerText = ticket.venue_name;
      document.getElementById('modal-buyer-name').innerText = ticket.buyer;
      document.getElementById('modal-event-date').innerText = ticket.created_at.split('T')[0];
      document.getElementById('modal-pass-qty').innerText = `${ticket.qty} Guest Pass(es)`;
      document.getElementById('modal-ticket-id').innerText = ticket.verification_hash;

      // Render QR Code
      const qrContainer = document.getElementById('qrcode-container');
      qrContainer.innerHTML = "";
      new QRCode(qrContainer, {
        text: ticket.verification_hash,
        width: 120,
        height: 120
      });

      document.getElementById('ticket-modal').classList.remove('hidden');
    }

    function closeTicketModal() {
      document.getElementById('ticket-modal').classList.add('hidden');
    }

    // ---------------------------------------------------------
    // 5. MODULE 2: VENUE OPERATIONS & METRICS
    // ---------------------------------------------------------
    function renderVenueOpsUI() {
      const venue = appData.venues[0];
      if (!venue) return;

      document.getElementById('ops-venue-name').value = venue.name;
      document.getElementById('ops-venue-capacity').value = venue.max_capacity;
      document.getElementById('ops-venue-whatsapp').value = venue.whatsapp_no;
      document.getElementById('ops-venue-tax').value = venue.tax_id;
      document.getElementById('ops-venue-bank').value = venue.bank_details;

      // Update Metrics
      document.getElementById('metric-bookings-count').innerText = appData.bookings.length;
      document.getElementById('metric-spaces-count').innerText = appData.spaces.length;
      
      const rev = appData.bookings.reduce((sum, b) => sum + (b.venue_cost || 0), 0);
      document.getElementById('metric-venue-revenue').innerText = `BWP ${rev.toLocaleString(undefined, {minimumFractionDigits:2})}`;
    }

    function saveVenueSettings(e) {
      e.preventDefault();
      const venue = appData.venues[0];
      if (!venue) return;

      venue.name = document.getElementById('ops-venue-name').value;
      venue.max_capacity = parseInt(document.getElementById('ops-venue-capacity').value);
      venue.whatsapp_no = document.getElementById('ops-venue-whatsapp').value;
      venue.tax_id = document.getElementById('ops-venue-tax').value;
      venue.bank_details = document.getElementById('ops-venue-bank').value;

      saveStorage();
      alert("Facility profile updated successfully!");
    }

    function publishPublicEvent(e) {
      e.preventDefault();
      const venue = appData.venues[0];

      const newEvent = {
        event_id: "EVT-" + Date.now(),
        venue_id: venue.venue_id,
        venue_name: venue.name,
        title: document.getElementById('ops-event-title').value,
        date: document.getElementById('ops-event-date').value,
        price: parseFloat(document.getElementById('ops-event-price').value),
        description: document.getElementById('ops-event-desc').value,
        flyer_url: document.getElementById('ops-event-flyer').value || SPACE_PRESETS[0]
      };

      appData.events.push(newEvent);
      saveStorage();
      renderPublicEvents();
      alert("Public event published to market hub!");
    }

    // ---------------------------------------------------------
    // 6. MODULE 3: VENDOR MANAGEMENT
    // ---------------------------------------------------------
    function renderVendorUI() {
      const tableBody = document.getElementById('vendor-orders-table-body');
      if (appData.vendor_invoices.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-xs text-slate-500">No vendor service orders currently dispatched.</td></tr>`;
        return;
      }

      tableBody.innerHTML = appData.vendor_invoices.map(inv => `
        <tr class="hover:bg-slate-50 text-xs">
          <td class="p-3 font-mono font-bold">${inv.vendor_invoice_id}</td>
          <td class="p-3">${inv.venue_name}</td>
          <td class="p-3">${inv.customer_name}<br><span class="text-slate-400">${inv.customer_email}</span></td>
          <td class="p-3">${inv.event_date}</td>
          <td class="p-3 font-bold">BWP ${inv.total_amount.toLocaleString()}</td>
          <td class="p-3"><span class="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">${inv.status}</span></td>
        </tr>
      `).join('');
    }

    function addVendorItem(e) {
      e.preventDefault();
      const supporter = appData.supporters[0];

      const newItem = {
        template_id: Date.now(),
        supporter_id: supporter.supporter_id,
        item_name: document.getElementById('vnd-item-name').value,
        unit_price: parseFloat(document.getElementById('vnd-item-price').value),
        unit_type: document.getElementById('vnd-item-unit').value,
        description: "Standard service package offering."
      };

      appData.vendor_templates.push(newItem);
      saveStorage();
      renderVendorAccordion();
      alert("Service package added to active catalog!");
    }

    // ---------------------------------------------------------
    // 7. MODULE 4: ACCESS CONTROL & VERIFICATION
    // ---------------------------------------------------------
    function verifyTicketPass() {
      const code = document.getElementById('scan-ticket-id').value.trim();
      const card = document.getElementById('scan-result-card');
      card.classList.remove('hidden');

      const ticket = appData.tickets.find(t => t.verification_hash === code || t.ticket_id === code);

      if (!ticket) {
        card.className = "p-4 rounded border text-center space-y-2 bg-rose-50 border-rose-300 text-rose-900";
        card.innerHTML = `
          <i class="fa-solid fa-circle-xmark text-3xl text-rose-600"></i>
          <h4 class="font-bold text-base">INVALID ADMISSION PASS</h4>
          <p class="text-xs">No active pass matched this hash or reference code.</p>
        `;
      } else if (ticket.status === "Scanned / Used") {
        card.className = "p-4 rounded border text-center space-y-2 bg-amber-50 border-amber-300 text-amber-900";
        card.innerHTML = `
          <i class="fa-solid fa-triangle-exclamation text-3xl text-amber-600"></i>
          <h4 class="font-bold text-base">PASS ALREADY REDEEMED</h4>
          <p class="text-xs">Ticket was previously scanned at: ${ticket.scanned_at}</p>
        `;
      } else {
        ticket.status = "Scanned / Used";
        ticket.scanned_at = new Date().toLocaleTimeString();
        saveStorage();

        card.className = "p-4 rounded border text-center space-y-2 bg-emerald-50 border-emerald-300 text-emerald-900";
        card.innerHTML = `
          <i class="fa-solid fa-circle-check text-3xl text-emerald-600"></i>
          <h4 class="font-bold text-base">ENTRY GRANTED</h4>
          <p class="text-xs"><strong>Event:</strong> ${ticket.event_title}</p>
          <p class="text-xs"><strong>Attendee:</strong> ${ticket.buyer} (${ticket.qty} Guest Pass)</p>
        `;
      }
    }

    // ---------------------------------------------------------
    // 8. MODULE 5: MASTER LEDGER
    // ---------------------------------------------------------
    function renderLedgerUI() {
      const tableBody = document.getElementById('ledger-table-body');
      if (appData.bookings.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-xs text-slate-500">No master bookings recorded in ledger.</td></tr>`;
        return;
      }

      tableBody.innerHTML = appData.bookings.map(b => `
        <tr class="hover:bg-slate-50 text-xs">
          <td class="p-3 font-mono font-bold">${b.booking_id}</td>
          <td class="p-3">${b.customer_name}<br><span class="text-slate-400">${b.customer_email}</span></td>
          <td class="p-3">${b.space_name} (${b.days} Days)</td>
          <td class="p-3">${b.booking_date}</td>
          <td class="p-3 font-bold">BWP ${b.venue_cost.toLocaleString()}</td>
          <td class="p-3"><span class="bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded">${b.status}</span></td>
          <td class="p-3">
            <button onclick="downloadVenuePDF('${b.booking_id}')" class="text-slate-900 hover:text-amber-600 font-bold">
              <i class="fa-solid fa-file-pdf"></i> PDF
            </button>
          </td>
        </tr>
      `).join('');
    }

    // ---------------------------------------------------------
    // 9. CLIENT-SIDE PDF INVOICE GENERATOR (jsPDF Engine)
    // ---------------------------------------------------------
    function downloadVenuePDF(bookingId) {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      const booking = appData.bookings.find(b => b.booking_id === bookingId);
      const venue = appData.venues.find(v => v.venue_id === booking.venue_id);

      // Header Branding
      doc.setFillColor(15, 23, 42); // slate-900
      doc.rect(0, 0, 210, 30, 'F');
      
      doc.setTextColor(255, 255, 255);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(16);
      doc.text("OFFICIAL TAX INVOICE", 14, 18);
      
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.text(venue.name.toUpperCase(), 14, 25);

      // Metadata Box
      doc.setTextColor(15, 23, 42);
      doc.setFontSize(9);
      doc.text(`Invoice Ref: ${booking.booking_id}`, 14, 42);
      doc.text(`Date Issued: ${booking.created_at}`, 14, 48);
      doc.text(`Tax / CIPA Reg ID: ${venue.tax_id}`, 14, 54);

      doc.text(`Billed To: ${booking.customer_name}`, 120, 42);
      doc.text(`Client Email: ${booking.customer_email}`, 120, 48);
      doc.text(`Contact Phone: ${booking.customer_phone}`, 120, 54);

      // Line Items Table Header
      doc.setFillColor(241, 245, 249);
      doc.rect(14, 65, 182, 8, 'F');
      doc.setFont("helvetica", "bold");
      doc.text("Description", 18, 70);
      doc.text("Days", 110, 70);
      doc.text("Rate (BWP)", 140, 70);
      doc.text("Total (BWP)", 170, 70);

      // Line Item
      doc.setFont("helvetica", "normal");
      doc.text(`Venue Hire: ${booking.space_name}`, 18, 80);
      doc.text(`${booking.days}`, 110, 80);
      doc.text(`${(booking.venue_cost / booking.days).toFixed(2)}`, 140, 80);
      doc.text(`${booking.venue_cost.toFixed(2)}`, 170, 80);

      // Divider & Total
      doc.line(14, 90, 196, 90);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.text("TOTAL DUE:", 120, 100);
      doc.text(`BWP ${booking.venue_cost.toLocaleString(undefined, {minimumFractionDigits: 2})}`, 170, 100);

      // Settlement Details
      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      doc.text("Bank Settlement Details:", 14, 115);
      doc.setFont("helvetica", "normal");
      doc.text(venue.bank_details, 14, 122);

      // Download Trigger
      doc.save(`Invoice_${booking.booking_id}.pdf`);
    }

    // ---------------------------------------------------------
    // INITIALIZATION ON LOAD
    // ---------------------------------------------------------
    window.addEventListener('DOMContentLoaded', () => {
      loadStorage();
      initMarketplaceUI();
    });
  </script>
</body>
</html>
