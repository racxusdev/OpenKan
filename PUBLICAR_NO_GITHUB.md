# Publicar o OpenKan no GitHub

O projeto já vem pronto para virar repositório público: `LICENSE` (MIT, sua
autoria), `README.md` (português), `README_EN.md` (inglês), `.gitignore`,
capturas de tela e verificação automática de compilação (`.github/workflows/ci.yml`).

## Passo a passo

1. **Crie o repositório no GitHub**
   Acesse <https://github.com/new> e crie um repositório chamado `OpenKan`
   (público), **sem** marcar "Add a README", ".gitignore" ou "license" —
   porque todos já vêm aqui dentro.

2. **Extraia o zip e entre na pasta do projeto**

   ```bash
   unzip OpenKan-v2.2.0.zip
   cd OpenKan-v2.2.0
   ```

3. **Publique**

   ```bash
   git init
   git add .
   git commit -m "OpenKan 2.2.0 — primeira versão pública"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/OpenKan.git
   git push -u origin main
   ```

   (troque `SEU_USUARIO` pelo seu usuário do GitHub)

4. **Capriche na página do repositório** (opcional, mas recomendo)
   - *Settings → About*: descrição curta — “Câmera com efeitos em tempo real
     para Ubuntu — Python + PyQt6 + OpenCV” — e o site do projeto, se tiver.
   - *Releases → Draft a new release*: tag `v2.2.0`, título “OpenKan 2.2.0”,
     e anexe o próprio zip para quem quiser baixar sem clonar.

## O que já está configurado

| Item | Onde | Estado |
| --- | --- | --- |
| Licença MIT (autoria Racxus Dev) | `LICENSE` | ✅ |
| README bilíngue com badges | `README.md` (inglês), `README_PT.md` (português) | ✅ |
| Ignorar lixo de build/venv | `.gitignore` | ✅ |
| CI (compilação automática) | `.github/workflows/ci.yml` | ✅ |
| Captura de tela | `captura_de_tela.png`, `captura_de_tela_en.png` | ✅ |
| Instalador/desinstalador | `install.sh`, `uninstall.sh` | ✅ |

## Dica: badge de doação no GitHub

O README já traz o badge do Ko-Fi apontando para <https://ko-fi.com/racxus>.
Se quiser, adicione também o link em *Settings → About → Website*.
