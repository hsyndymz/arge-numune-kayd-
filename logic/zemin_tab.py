import streamlit as st
import streamlit.components.v1 as components

def render_zemin_tab():
    st.title("🌍 ZEMİN KARAR SİSTEMİ (Zemin Pro)")
    st.markdown("""
    **Zemin Pro React Arayüzü**, doğrudan uygulamanıza gömülü olarak ağ üzerinden çalışır. 
    Arayüzün yüklenmemesi durumunda, lütfen sunucu (ana bilgisayar) üzerinde sistemin (`npm run dev --host`) başlatıldığından emin olun.
    """)
    
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    # Sunucunun ağ üzerindeki dinamik IP adresi ve 5173 portunu otomatik algılaması için Javascript kullanıyoruz.
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>body { margin: 0; padding: 0; background: transparent; overflow: hidden; }</style>
    </head>
    <body>
        <div id="status-msg" style="color: #666; font-family: sans-serif; padding: 20px; display: none;">
            Zemin Pro Arayüzüne bağlanılamıyor. Lütfen ana bilgisayarda NPM sunucusunun açık olduğunu kontrol edin.
        </div>
        <script>
            // Streamlit sandbox icinde dogru IP uzerinden calisabilmesi icin hiyerarsik kontrol
            function getHost() {
                try {
                    // 1. Parent window hostname (en guveniliri)
                    if (window.parent && window.parent.location.hostname != "") {
                        return window.parent.location.hostname;
                    }
                } catch(e) {}
                
                // 2. Kendi hostname'i (sandbox'a bagli degisir)
                if (window.location.hostname && window.location.hostname != "") {
                    return window.location.hostname;
                }
                
                // 3. Varsayilan (sadece local'de calisir)
                return "localhost";
            }

            var host = getHost();
            var reactUrl = "http://" + host + ":5173";
            
            var iframe = document.createElement('iframe');
            iframe.src = reactUrl;
            iframe.width = "100%";
            iframe.height = "800px";
            iframe.style.border = "none";
            iframe.style.borderRadius = "8px";
            iframe.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
            
            // Yukleme hatasi kontrolu
            iframe.onerror = function() {
                document.getElementById('status-msg').style.display = 'block';
            };

            document.body.appendChild(iframe);
        </script>
    </body>
    </html>
    """
    
    # 800px yüksekliğinde, scroll edilebilen bir pencere açar
    components.html(html_code, height=820, scrolling=True)
