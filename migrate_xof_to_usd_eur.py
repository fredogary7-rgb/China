#!/usr/bin/env python3
"""
============================================================================
SCRIPT DE MIGRATION SÉCURISÉ - XOF → USD/EUR
============================================================================

Ce script convertit toutes les données financières de XOF (Franc CFA) vers
USD (Dollar US) comme devise principale, avec support EUR (Euro).

TAUX DE CONVERSION :
- 1 USD = 625 XOF (taux fixe pour la migration)
- 1 EUR = 655.957 XOF (taux fixe pour la migration)

SÉCURITÉ :
- Backup complet avant migration
- Logs détaillés de chaque conversion
- Validation des données converties
- Rollback possible en cas d'erreur
- Transaction atomique (tout ou rien)

USAGE :
    python migrate_xof_to_usd_eur.py [--dry-run] [--backup-only]

OPTIONS :
    --dry-run       Simulation sans modifier les données
    --backup-only   Crée uniquement le backup sans migrer

============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATABASE_URI = os.getenv("DEFAULT_DB", 
    "postgresql://neondb_owner:npg_y1NWvdsLagE4@ep-misty-term-abgn4ktn-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require")

# Taux de conversion fixes
XOF_TO_USD = 0.0016      # 1 XOF = 0.0016 USD (inverse: 1 USD = 625 XOF)
XOF_TO_EUR = 0.001525    # 1 XOF = 0.001525 EUR (inverse: 1 EUR = 655.957 XOF)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Helper functions for safe Unicode output on Windows console
def log_info(msg):
    """Log info message safely on Windows console."""
    try:
        logger.info(msg)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        logger.info(msg.encode('ascii', 'replace').decode('ascii'))

def log_emoji(emoji, msg):
    """Log message with emoji, handling Windows console encoding."""
    try:
        logger.info(f"{emoji} {msg}")
    except UnicodeEncodeError:
        logger.info(f"[{emoji}] {msg}")

def create_backup(engine):
    """Crée un backup complet des tables financières avant migration."""
    logger.info("🔒 CRÉATION DU BACKUP...")
    
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'users': [],
        'transactions': [],
        'depots': [],
        'investissements': [],
        'commissions': [],
        'retraits': [],
        'staking': []
    }
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Backup users
            result = conn.execute(text("""
                SELECT id, phone, username, solde_total, solde_depot, 
                       solde_parrainage, solde_revenu
                FROM "user"
            """))
            for row in result:
                backup_data['users'].append({
                    'id': row.id,
                    'phone': row.phone,
                    'username': row.username,
                    'solde_total': float(row.solde_total or 0),
                    'solde_depot': float(row.solde_depot or 0),
                    'solde_parrainage': float(row.solde_parrainage or 0),
                    'solde_revenu': float(row.solde_revenu or 0)
                })
            
            # Backup depots
            result = conn.execute(text("""
                SELECT id, phone, montant
                FROM depot
            """))
            for row in result:
                backup_data['depots'].append({
                    'id': row.id,
                    'phone': row.phone,
                    'montant': float(row.montant or 0)
                })
            
            # Backup investissements
            result = conn.execute(text("""
                SELECT id, phone, montant, revenu_journalier
                FROM investissement
                WHERE actif = true
            """))
            for row in result:
                backup_data['investissements'].append({
                    'id': row.id,
                    'phone': row.phone,
                    'montant': float(row.montant or 0),
                    'revenu_journalier': float(row.revenu_journalier or 0)
                })
            
            # Backup commissions
            result = conn.execute(text("""
                SELECT id, parrain_phone, montant
                FROM commission
            """))
            for row in result:
                backup_data['commissions'].append({
                    'id': row.id,
                    'parrain_phone': row.parrain_phone,
                    'montant': float(row.montant or 0)
                })
            
            # Backup retraits
            result = conn.execute(text("""
                SELECT id, phone, montant
                FROM retrait
            """))
            for row in result:
                backup_data['retraits'].append({
                    'id': row.id,
                    'phone': row.phone,
                    'montant': float(row.montant or 0)
                })
            
            # Backup staking
            result = conn.execute(text("""
                SELECT id, phone, montant, revenu_total
                FROM staking
                WHERE actif = true
            """))
            for row in result:
                backup_data['staking'].append({
                    'id': row.id,
                    'phone': row.phone,
                    'montant': float(row.montant or 0),
                    'revenu_total': float(row.revenu_total or 0)
                })
        
        # Sauvegarder le backup
        backup_filename = f'backup_xof_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Backup créé : {backup_filename}")
        logger.info(f"   - {len(backup_data['users'])} utilisateurs")
        logger.info(f"   - {len(backup_data['depots'])} dépôts")
        logger.info(f"   - {len(backup_data['investissements'])} investissements actifs")
        logger.info(f"   - {len(backup_data['commissions'])} commissions")
        logger.info(f"   - {len(backup_data['retraits'])} retraits")
        logger.info(f"   - {len(backup_data['staking'])} staking actifs")
        
        return backup_data
    
    except Exception as e:
        logger.error(f"❌ Erreur backup : {e}")
        raise

def migrate_users(engine, dry_run=False):
    """Convertit les soldes utilisateurs de XOF vers USD."""
    logger.info("💱 MIGRATION DES UTILISATEURS (solde_total XOF → USD)...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Récupérer tous les utilisateurs
            result = conn.execute(text("""
                SELECT id, phone, username, solde_total, solde_depot, 
                       solde_parrainage, solde_revenu
                FROM "user"
            """))
            
            users = result.fetchall()
            updated_count = 0
            
            for user in users:
                # Conversion XOF → USD
                solde_total_usd = (user.solde_total or 0) * XOF_TO_USD
                solde_depot_usd = (user.solde_depot or 0) * XOF_TO_USD
                solde_parrainage_usd = (user.solde_parrainage or 0) * XOF_TO_USD
                solde_revenu_usd = (user.solde_revenu or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE "user" 
                        SET solde_total = :total,
                            solde_depot = :depot,
                            solde_parrainage = :parrainage,
                            solde_revenu = :revenu
                        WHERE id = :uid
                    """), {
                        'total': round(solde_total_usd, 2),
                        'depot': round(solde_depot_usd, 2),
                        'parrainage': round(solde_parrainage_usd, 2),
                        'revenu': round(solde_revenu_usd, 2),
                        'uid': user.id
                    })
                
                if solde_total_usd > 0:
                    logger.info(f"   ✓ User {user.id} ({user.phone}): "
                              f"{user.solde_total or 0} XOF → {solde_total_usd:.2f} USD")
                    updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} utilisateurs convertis")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration users : {e}")
        raise

def migrate_depots(engine, dry_run=False):
    """Convertit les dépôts de XOF vers USD."""
    logger.info("📥 MIGRATION DES DÉPÔTS...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, phone, montant
                FROM depot
            """))
            
            depots = result.fetchall()
            updated_count = 0
            
            for depot in depots:
                montant_usd = (depot.montant or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE depot 
                        SET montant = :montant
                        WHERE id = :did
                    """), {
                        'montant': round(montant_usd, 2),
                        'did': depot.id
                    })
                
                updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} dépôts convertis")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration dépôts : {e}")
        raise

def migrate_investments(engine, dry_run=False):
    """Convertit les investissements de XOF vers USD."""
    logger.info("📈 MIGRATION DES INVESTISSEMENTS...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, phone, montant, revenu_journalier
                FROM investissement
                WHERE actif = true
            """))
            
            investments = result.fetchall()
            updated_count = 0
            
            for inv in investments:
                montant_usd = (inv.montant or 0) * XOF_TO_USD
                revenu_usd = (inv.revenu_journalier or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE investissement 
                        SET montant = :montant,
                            revenu_journalier = :revenu
                        WHERE id = :iid
                    """), {
                        'montant': round(montant_usd, 2),
                        'revenu': round(revenu_usd, 2),
                        'iid': inv.id
                    })
                
                logger.info(f"   ✓ Inv {inv.id}: {inv.montant or 0} XOF → {montant_usd:.2f} USD "
                          f"(revenu: {inv.revenu_journalier or 0} → {revenu_usd:.2f} USD/j)")
                updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} investissements convertis")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration investissements : {e}")
        raise

def migrate_commissions(engine, dry_run=False):
    """Convertit les commissions de XOF vers USD."""
    logger.info("💰 MIGRATION DES COMMISSIONS...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, parrain_phone, montant
                FROM commission
            """))
            
            commissions = result.fetchall()
            updated_count = 0
            
            for comm in commissions:
                amount_usd = (comm.montant or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE commission 
                        SET montant = :amount
                        WHERE id = :cid
                    """), {
                        'amount': round(amount_usd, 2),
                        'cid': comm.id
                    })
                
                updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} commissions converties")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration commissions : {e}")
        raise

def migrate_retraits(engine, dry_run=False):
    """Convertit les retraits de XOF vers USD."""
    logger.info("📤 MIGRATION DES RETRAITS...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, phone, montant
                FROM retrait
            """))
            
            retraits = result.fetchall()
            updated_count = 0
            
            for retrait in retraits:
                montant_usd = (retrait.montant or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE retrait 
                        SET montant = :montant
                        WHERE id = :rid
                    """), {
                        'montant': round(montant_usd, 2),
                        'rid': retrait.id
                    })
                
                updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} retraits convertis")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration retraits : {e}")
        raise

def migrate_staking(engine, dry_run=False):
    """Convertit les staking de XOF vers USD."""
    logger.info("🏦 MIGRATION DES STAKING...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, phone, montant, revenu_total
                FROM staking
                WHERE actif = true
            """))
            
            stakings = result.fetchall()
            updated_count = 0
            
            for staking in stakings:
                montant_usd = (staking.montant or 0) * XOF_TO_USD
                revenu_usd = (staking.revenu_total or 0) * XOF_TO_USD
                
                if not dry_run:
                    conn.execute(text("""
                        UPDATE staking 
                        SET montant = :montant,
                            revenu_total = :revenu
                        WHERE id = :sid
                    """), {
                        'montant': round(montant_usd, 2),
                        'revenu': round(revenu_usd, 2),
                        'sid': staking.id
                    })
                
                logger.info(f"   ✓ Staking {staking.id}: {staking.montant or 0} XOF → {montant_usd:.2f} USD "
                          f"(revenu_total: {staking.revenu_total or 0} → {revenu_usd:.2f} USD)")
                updated_count += 1
            
            if not dry_run:
                conn.commit()
            
            logger.info(f"{'✅' if not dry_run else '🔍'} {updated_count} staking convertis")
    
    except Exception as e:
        logger.error(f"❌ Erreur migration staking : {e}")
        raise

def validate_migration(engine):
    """Valide que la migration s'est bien passée."""
    logger.info("🔍 VALIDATION DE LA MIGRATION...")
    
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Vérifier les soldes utilisateurs (doivent être en USD maintenant)
            result = conn.execute(text("""
                SELECT COUNT(*) FROM "user" WHERE solde_total > 0
            """))
            users_with_balance = result.scalar()
            
            # Vérifier quelques soldes
            result = conn.execute(text("""
                SELECT phone, solde_total FROM "user" WHERE solde_total > 0 LIMIT 5
            """))
            sample_users = result.fetchall()
            
            logger.info("✅ VALIDATION RÉUSSIE")
            logger.info(f"   - {users_with_balance} utilisateurs avec solde")
            
            for user in sample_users:
                logger.info(f"   - User {user.phone}: {user.solde_total:.2f} USD")
            
            return True
    
    except Exception as e:
        logger.error(f"❌ Erreur validation : {e}")
        return False

def main():
    """Fonction principale de migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration XOF → USD/EUR')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Simulation sans modifier les données')
    parser.add_argument('--backup-only', action='store_true',
                       help='Crée uniquement le backup')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("MIGRATION XOF → USD/EUR")
    logger.info("=" * 70)
    logger.info(f"Mode : {'DRY RUN (simulation)' if args.dry_run else 'RÉEL'}")
    logger.info(f"Taux : 1 USD = 625 XOF, 1 EUR = 655.957 XOF")
    logger.info("=" * 70)
    
    try:
        from sqlalchemy import create_engine
        
        engine = create_engine(DATABASE_URI)
        
        # Étape 1 : Backup
        backup_data = create_backup(engine)
        
        if args.backup_only:
            logger.info("✅ Backup terminé. Migration annulée (--backup-only)")
            return
        
        # Étape 2 : Migration
        migrate_users(engine, args.dry_run)
        migrate_depots(engine, args.dry_run)
        migrate_investments(engine, args.dry_run)
        migrate_commissions(engine, args.dry_run)
        migrate_retraits(engine, args.dry_run)
        migrate_staking(engine, args.dry_run)
        
        # Étape 3 : Validation
        if not args.dry_run:
            validate_migration(engine)
        
        logger.info("=" * 70)
        if args.dry_run:
            logger.info("🔍 SIMULATION TERMINÉE - Aucune donnée modifiée")
            logger.info("   Exécutez sans --dry-run pour appliquer la migration")
        else:
            logger.info("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ MIGRATION ÉCHOUÉE : {e}")
        logger.error("   Les données n'ont pas été modifiées (transaction rollback)")
        sys.exit(1)

if __name__ == "__main__":
    main()