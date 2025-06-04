$entity = "light.lampada_quarto_localtuya"
$token = "PEGARNOARQUIVO .env"
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
    "rgb_color" = @(255, 255, 255)
    "brightness" = 1000 # brilho máximo
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://homeassistant.local:8123/api/services/light/turn_on" -Method POST -Headers $headers -Body $body

# Desligar a lâmpada ao final
$body = @{
    "entity_id" = $entity
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://homeassistant.local:8123/api/services/light/turn_on" -Method POST -Headers $headers -Body $body