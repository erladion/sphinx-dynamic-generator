:content_order: 5
:content_title: HTML Analytics Dashboard

Raw HTML Content Example
====================================

This file contains content written entirely in HTML, which Sphinx will only output
in the HTML build and skip during the PDF build.

**1. HTML Version (Web Only)**

.. only:: html

   .. raw:: html

      <div style="padding: 20px; border: 2px solid #2980B9; border-radius: 8px; margin-top: 20px;">
          <h2 style="color: #2980B9;">Live Data Report (HTML Only)</h2>
          <p>This content is designed for web display and uses custom HTML structure.</p>
          
          <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
              <thead>
                  <tr style="background-color: #ecf0f1;">
                      <th style="padding: 8px; border: 1px solid #bdc3c7;">Metric</th>
                      <th style="padding: 8px; border: 1px solid #bdc3c7;">Value</th>
                  </tr>
              </thead>
              <tbody>
                  <tr>
                      <td style="padding: 8px; border: 1px solid #bdc3c7;">Page Views</td>
                      <td style="padding: 8px; border: 1px solid #bdc3c7;">1,245</td>
                  </tr>
                  <tr style="background-color: #f7f9fb;">
                      <td style="padding: 8px; border: 1px solid #bdc3c7;">Conversion Rate</td>
                      <td style="padding: 8px; border: 1px solid #bdc3c7;">4.2%</td>
                  </tr>
              </tbody>
          </table>
      </div>

**2. LaTeX/PDF Version (Print Only)**

.. only:: latex

   .. container:: custom-data-table
   
      .. table:: Analytics Summary
         :widths: 30 70

         +-----------------+---------------------+
         | Metric          | Value               |
         +=================+=====================+
         | Page Views      | 1,245               |
         +-----------------+---------------------+
         | Conversion Rate | 4.2\%               |
         +-----------------+---------------------+