"""
Service de génération de pick-list PDF pour les rouleaux sélectionnés.
"""

import os
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PickListService:
    """Service pour générer les pick-lists PDF."""
    
    def __init__(self):
        self.export_dir = os.path.join(settings.MEDIA_ROOT, 'pick-lists')
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Styles
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Créer les styles personnalisés."""
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0056b3')
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#333333')
        ))
        
        # Style info
        self.styles.add(ParagraphStyle(
            name='InfoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
    
    def generate_pick_list_pdf(self, rolls_data, report_name):
        """
        Génère un PDF de pick-list avec les données des rouleaux.
        
        Args:
            rolls_data: Dictionnaire contenant les données des rouleaux
            report_name: Nom du fichier (format S2212001)
            
        Returns:
            tuple: (success: bool, file_path: str, message: str)
        """
        try:
            filename = f"{report_name}.pdf"
            filepath = os.path.join(self.export_dir, filename)
            
            # Créer le document PDF
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Construire le contenu
            story = []
            
            # En-tête avec logo Saint-Gobain (si disponible)
            story.extend(self._build_header(report_name))
            
            # Informations générales
            story.extend(self._build_summary(rolls_data))
            
            # Tableau des rouleaux
            story.extend(self._build_rolls_table(rolls_data['rolls']))
            
            # Détails des contrôles qualité
            story.extend(self._build_quality_details(rolls_data['rolls']))
            
            # Pied de page avec signature
            story.extend(self._build_footer())
            
            # Générer le PDF
            doc.build(story)
            
            return True, filepath, f"Pick-list {filename} générée avec succès"
            
        except Exception as e:
            return False, "", f"Erreur lors de la génération: {str(e)}"
    
    def _build_header(self, report_name):
        """Construire l'en-tête du document."""
        elements = []
        
        # Titre principal
        title = Paragraph(
            f"PICK-LIST - {report_name}",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Informations générales
        date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
        info = Paragraph(
            f"<b>Saint-Gobain Quartz - Ligne G</b><br/>"
            f"Généré le {date_str}",
            self.styles['InfoStyle']
        )
        elements.append(info)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_summary(self, rolls_data):
        """Construire le résumé de la pick-list."""
        elements = []
        
        # Titre section
        subtitle = Paragraph("RÉSUMÉ", self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # Données de résumé
        summary_data = [
            ['Nombre de rouleaux:', str(rolls_data['rolls_count'])],
            ['Longueur totale:', f"{rolls_data['total_length']:.2f} m"],
            ['Ordres de Fabrication:', ', '.join(rolls_data['unique_ofs'])],
            ['Date de génération:', datetime.now().strftime("%d/%m/%Y %H:%M")]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_rolls_table(self, rolls):
        """Construire le tableau principal des rouleaux."""
        elements = []
        
        # Titre section
        subtitle = Paragraph("LISTE DES ROULEAUX", self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # En-têtes du tableau
        headers = [
            'Roll ID', 'OF', 'Longueur\n(m)', 'Épaisseur Moy.\n(mm)', 'Grammage\n(g/m)',
            'Date Prod.', 'Opérateur', 'Défauts'
        ]
        
        # Données du tableau
        table_data = [headers]
        
        for roll in rolls:
            # Épaisseur moyenne
            ep_left = roll.get('avg_thickness_left')
            ep_right = roll.get('avg_thickness_right')
            
            if ep_left and ep_right:
                ep_moy = f"G:{ep_left:.3f}\nD:{ep_right:.3f}"
            elif ep_left:
                ep_moy = f"G:{ep_left:.3f}"
            elif ep_right:
                ep_moy = f"D:{ep_right:.3f}"
            else:
                ep_moy = "-"
            
            # Défauts
            defects_info = "Aucun" if not roll.get('defects') else f"{len(roll['defects'])} défaut(s)"
            
            row = [
                roll.get('roll_id', ''),
                roll.get('fabrication_order', ''),
                f"{roll.get('length', 0):.2f}" if roll.get('length') else '-',
                ep_moy,
                f"{roll.get('grammage_calc', 0):.1f}" if roll.get('grammage_calc') else '-',
                datetime.fromisoformat(roll['production_date']).strftime('%d/%m/%Y') if roll.get('production_date') else '',
                roll.get('operator', ''),
                defects_info
            ]
            
            table_data.append(row)
        
        # Créer le tableau
        col_widths = [2.5*cm, 1.5*cm, 2*cm, 2.5*cm, 2*cm, 2*cm, 3*cm, 2*cm]
        rolls_table = Table(table_data, colWidths=col_widths)
        
        # Style du tableau
        table_style = [
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Corps du tableau
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        
        rolls_table.setStyle(TableStyle(table_style))
        elements.append(rolls_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_quality_details(self, rolls):
        """Construire les détails des contrôles qualité."""
        elements = []
        
        # Titre section
        subtitle = Paragraph("DÉTAILS CONTRÔLES QUALITÉ", self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # Vérifier s'il y a des contrôles qualité
        has_quality_controls = any(roll.get('quality_controls') for roll in rolls)
        
        if not has_quality_controls:
            no_controls = Paragraph("Aucun contrôle qualité disponible pour ces rouleaux.", self.styles['InfoStyle'])
            elements.append(no_controls)
            elements.append(Spacer(1, 20))
            return elements
        
        # Tableau des contrôles qualité
        qc_headers = [
            'Roll ID', 'Micromètre G', 'Micromètre D', 'Masse Surf. G', 
            'Masse Surf. D', 'Extrait Sec (%)', 'LOI'
        ]
        
        qc_data = [qc_headers]
        
        for roll in rolls:
            qc = roll.get('quality_controls')
            if qc:
                row = [
                    roll.get('roll_id', ''),
                    f"{qc.get('micrometer_left_avg', 0):.3f}" if qc.get('micrometer_left_avg') else '-',
                    f"{qc.get('micrometer_right_avg', 0):.3f}" if qc.get('micrometer_right_avg') else '-',
                    f"{qc.get('surface_mass_left_avg', 0):.6f}" if qc.get('surface_mass_left_avg') else '-',
                    f"{qc.get('surface_mass_right_avg', 0):.6f}" if qc.get('surface_mass_right_avg') else '-',
                    f"{qc.get('dry_extract', 0):.3f}" if qc.get('dry_extract') else '-',
                    'Oui' if qc.get('loi_given') else 'Non'
                ]
                qc_data.append(row)
        
        if len(qc_data) > 1:  # Si on a des données en plus des en-têtes
            qc_col_widths = [2.5*cm, 2*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm, 1.5*cm]
            qc_table = Table(qc_data, colWidths=qc_col_widths)
            
            qc_table.setStyle(TableStyle([
                # En-têtes
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                
                # Corps
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                
                # Bordures
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(qc_table)
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _build_footer(self):
        """Construire le pied de page avec signature."""
        elements = []
        
        elements.append(Spacer(1, 30))
        
        # Zone de signature
        signature_text = Paragraph(
            "<b>Contrôlé par:</b> __________________________ &nbsp;&nbsp;&nbsp;&nbsp; "
            "<b>Date:</b> ________________ &nbsp;&nbsp;&nbsp;&nbsp; "
            "<b>Signature:</b> __________________________",
            self.styles['InfoStyle']
        )
        elements.append(signature_text)
        
        # Note de bas de page
        elements.append(Spacer(1, 20))
        footer_note = Paragraph(
            "<i>Document généré automatiquement par le système SGQ Ligne G - Saint-Gobain Quartz</i>",
            ParagraphStyle(
                name='FooterNote',
                parent=self.styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        )
        elements.append(footer_note)
        
        return elements
    
    def get_export_url(self, filename):
        """Retourner l'URL de téléchargement du fichier généré."""
        return f"/media/pick-lists/{filename}"