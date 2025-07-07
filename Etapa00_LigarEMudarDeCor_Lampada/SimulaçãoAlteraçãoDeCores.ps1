#Scripts para simular a alteração de cores de uma lâmpada e outras operações relacionadas em Home Assistant usando PowerShell
# Certifique-se de que o PowerShell está configurado para permitir a execução de scripts

$entity = "light.lampada_escritorio_2"
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiYTllNGZkMThiZWE0MWZlYTQ2MzgzNWZhMTI1ZjlhNyIsImlhdCI6MTc1MTY4MjQ0OCwiZXhwIjoyMDY3MDQyNDQ4fQ.1jdkkpen_ZVyyNTcsbhPrs4XkK5t4jSAAgBMjYGprMA"
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

# Definir as cores e o brilho
$colors = @(
    @(255, 0, 250), # rosa
    @(255, 255, 0), # azul claro
    @(0, 255, 255), # azul médio
    @(255, 60, 255)  # azul escuro
)

# Loop para alterar as cores
for ($i = 0; $i -lt 5; $i++) { # Altere o número de repetições conforme necessário
    foreach ($color in $colors) {
        $body = @{
            "entity_id" = $entity
            "rgb_color" = $color
            "brightness" = 1000 # brilho máximo
        } | ConvertTo-Json

        Invoke-WebRequest -Uri "http://homeassistant.local:8123/api/services/light/turn_on" -Method POST -Headers $headers -Body $body

        Start-Sleep -Milliseconds 250
    }
}

# Desligar a lâmpada ao final
$body = @{
    "entity_id" = $entity
    # cor branca
    "color_temp" = 153
    "brightness_pct" = 100
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://homeassistant.local:8123/api/services/light/turn_on" -Method POST -Headers $headers -Body $body


# Exemplo de uso do template para obter o estado de uma lâmpada específica
$respostaUmaLampada = Invoke-RestMethod -Uri "http://homeassistant.local:8123/api/states/light.$entity" -Method GET -Headers @{ "Authorization" = "Bearer $token" }
$respostaUmaLampada | ConvertTo-Json -Depth 99 > resposta_uma_lampada.json

# Exemplo de uso do template para obter o estado das luzes em uma área específica
$resposta = Invoke-RestMethod -Uri "http://homeassistant.local:8123/api/template" -Method POST -Headers @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" } -Body @"
{
  "template": "{ \"areas\": [ {% set comma = namespace(needed=false) %}{% for area in areas() %}{% set lights = area_entities(area) | select('search', '^light\\.') | list %}{% if lights %}{% if comma.needed %},{% endif %}{ \"area_name\": \"{{ area_name(area) }}\", \"area_id\": \"{{ area }}\", \"lights\": [ {% for light in lights %}{ \"entity_id\": \"{{ light }}\", \"state\": \"{{ states(light) }}\" }{{ \",\" if not loop.last }}{% endfor %} ] }{% set comma.needed = true %}{% endif %}{% endfor %} ] }"
}
"@
$resposta | ConvertTo-Json -Depth 99 > resposta.json