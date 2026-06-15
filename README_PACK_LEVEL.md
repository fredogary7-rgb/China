# 📦 Système Pack Level - Guide Complet

## 🎯 Principe de Base

**1 produit acheté = 1 fichier téléchargeable**

Le système de `pack_level` permet de contrôler l'accès aux fichiers PDF de la section Agriculture en fonction du nombre d'investissements réalisés par l'utilisateur.

## 📊 Règles de Calcul

| Nombre d'investissements | Pack Level | Fichiers téléchargeables |
|-------------------------|------------|-------------------------|
| 0                       | 0          | 0 (aucun accès)         |
| 1                       | 1          | 1 fichier               |
| 2                       | 2          | 2 fichiers              |
| 3                       | 3          | 3 fichiers              |
| 4                       | 4          | 4 fichiers              |
| 5+                      | 5          | Illimité                |

## ⚠️ Caractéristiques Importantes

1. **Cumulatif** : Le pack_level est basé sur le **nombre TOTAL** d'investissements (actifs + terminés)
2. **Non-régressif** : Le pack_level **ne diminue jamais**. Une fois atteint, un niveau est conservé même si les investissements expirent
3. **Automatique** : Le calcul se fait automatiquement via le script `update_pack_level_cumulatif.py`

## 🛠️ Fichiers et Scripts

### Scripts de Migration

1. **`add_pack_level_column.py`**
   - Ajoute la colonne `pack_level` à la table `user` si elle n'existe pas
   - À exécuter une seule fois lors de la mise en place initiale
   ```bash
   python add_pack_level_column.py
   ```

2. **`update_pack_level_cumulatif.py`** ⭐ (NOUVEAU)
   - Met à jour le `pack_level` de tous les utilisateurs
   - Basé sur le nombre TOTAL d'investissements
   - Respecte la règle de non-régression
   ```bash
   python update_pack_level_cumulatif.py
   ```

3. **`update_pack_levels.py`** (ANCIEN - à ne plus utiliser)
   - Ancien script basé uniquement sur les investissements **actifs**
   - Remplacé par `update_pack_level_cumulatif.py`

### Fichiers Modifiés

1. **`templates/agriculture.html`**
   - Affiche le pack_level actuel et le nombre de fichiers disponibles
   - Interface utilisateur mise à jour pour refléter la nouvelle logique
   - Messages adaptés pour pack_level 0, 1, 2, 3, 4, 5+

2. **`app.py`**
   - Les routes existantes fonctionnent toujours
   - L'API `/api/agriculture/download/<pdf_id>` vérifie le pack_level
   - L'API `/api/user/pack-level` retourne le niveau actuel

## 🚀 Utilisation

### Pour les Développeurs

1. **Initialisation** (une seule fois) :
   ```bash
   python add_pack_level_column.py
   ```

2. **Mise à jour régulière** (à exécuter périodiquement) :
   ```bash
   python update_pack_level_cumulatif.py
   ```

3. **Vérification** :
   - Consulter les logs pour voir les utilisateurs mis à jour
   - Vérifier le pack_level dans la base de données

### Pour les Utilisateurs

1. **Acheter un produit** → Le pack_level augmente automatiquement
2. **Accéder à `/academy/agriculture`** → Voir le nombre de fichiers disponibles
3. **Télécharger des PDFs** → Dans la limite du pack_level

## 📝 Exemple de Workflow

1. **Utilisateur A** achète 1 produit → pack_level = 1 → 1 fichier téléchargeable
2. **Utilisateur A** achète un 2ème produit → pack_level = 2 → 2 fichiers téléchargeables
3. **Utilisateur A** achète un 3ème produit → pack_level = 3 → 3 fichiers téléchargeables
4. **Utilisateur A** termine ses investissements → pack_level reste à 3 (ne diminue pas)

## 🔍 Vérification

Pour vérifier le pack_level d'un utilisateur :

```sql
SELECT phone, pack_level FROM "user" WHERE phone = 'numero_telephone';
```

Pour voir la distribution des pack_levels :

```sql
SELECT pack_level, COUNT(*) as user_count 
FROM "user" 
GROUP BY pack_level 
ORDER BY pack_level;
```

## 🆘 Dépannage

### Le pack_level ne se met pas à jour

1. Vérifier que la colonne `pack_level` existe :
   ```bash
   python add_pack_level_column.py
   ```

2. Exécuter le script de mise à jour :
   ```bash
   python update_pack_level_cumulatif.py
   ```

3. Vérifier les logs pour les erreurs

### Un utilisateur a un pack_level incorrect

1. Vérifier le nombre d'investissements dans la base de données :
   ```sql
   SELECT COUNT(*) FROM investissement WHERE phone = 'numero_telephone';
   ```

2. Comparer avec le pack_level actuel

3. Si nécessaire, mettre à jour manuellement (admin seulement) :
   ```sql
   UPDATE "user" SET pack_level = nouveau_niveau WHERE phone = 'numero_telephone';
   ```

## 📞 Support

Pour toute question ou problème, contacter l'équipe de développement.

---

**Dernière mise à jour** : 15/06/2026
**Version** : 2.0 (Système cumulatif 1 produit = 1 fichier)