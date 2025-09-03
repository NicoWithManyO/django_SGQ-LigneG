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
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics import renderPDF
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
            fontSize=22,
            spaceAfter=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0E4E95'),
            fontName='Helvetica-Bold'
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=10,
            alignment=TA_LEFT,
            textColor=colors.HexColor('#EC1846'),
            fontName='Helvetica-Bold'
        ))
        
        # Style info
        self.styles.add(ParagraphStyle(
            name='InfoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Style adresse élégant
        self.styles.add(ParagraphStyle(
            name='AddressStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica'
        ))
        
        # Style référence
        self.styles.add(ParagraphStyle(
            name='RefStyle',
            parent=self.styles['Normal'],
            fontSize=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#EC1846'),
            spaceBefore=10,
            spaceAfter=25,
            fontName='Helvetica-Bold'
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
            
            # Moyennes générales
            story.extend(self._build_averages_summary(rolls_data['rolls']))
            
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
        """Construire l'en-tête du document avec logo SGQ et gradient."""
        elements = []
        
        # Ajouter le logo logoForPDF.png à la racine
        logo_path = os.path.join(settings.BASE_DIR, 'logoForPDF.png')
        logo_loaded = False
        
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=3*cm, height=1.3*cm)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 15))
                logo_loaded = True
            except Exception as e:
                print(f"Erreur chargement logo {logo_path}: {e}")
        
        if not logo_loaded:
            # Si le logo ne peut pas être chargé, ajouter juste le titre SGQ
            title_sgq = Paragraph(
                "<b><font size=18 color='#0E4E95'>SGQ Ligne G</font></b><br/>"
                "<font size=12 color='#2c3e50'>Saint-Gobain Quartz</font>",
                ParagraphStyle(
                    name='SGQTitle',
                    parent=self.styles['Normal'],
                    alignment=TA_CENTER,
                    spaceBefore=15,
                    spaceAfter=15
                )
            )
            elements.append(title_sgq)
        
        # Barre de couleur gradient Saint-Gobain
        gradient_bar = self._create_gradient_bar()
        elements.append(gradient_bar)
        elements.append(Spacer(1, 15))
        
        # Titre principal avec style amélioré
        title = Paragraph(
            "<b><font size=24>RELEVÉ DE CONTRÔLES</font></b>",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Référence du relevé avec encadré
        reference = Paragraph(
            f"<b><font size=18>Pré-shipper : {report_name}</font></b>",
            self.styles['RefStyle']
        )
        elements.append(reference)
        
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
        
        summary_table = Table(summary_data, colWidths=[5*cm, 9*cm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0E4E95')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
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
        
        # En-têtes du tableau (sans colonne Défauts)
        headers = [
            'Roll ID', 'OF', 'Longueur\n(m)', 'Épaisseur Moy. (mm)', 'Grammage\n(g/m²)',
            'Date Prod.'
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
            
            row = [
                roll.get('roll_id', ''),
                roll.get('fabrication_order', ''),
                f"{roll.get('length', 0):.2f}" if roll.get('length') else '-',
                ep_moy,
                f"{roll.get('grammage_calc', 0):.1f}" if roll.get('grammage_calc') else '-',
                datetime.fromisoformat(roll['production_date']).strftime('%d/%m/%Y') if roll.get('production_date') else ''
            ]
            
            table_data.append(row)
        
        # Créer le tableau (sans colonne Défauts)
        col_widths = [3*cm, 2*cm, 2.5*cm, 3*cm, 2.5*cm, 2.5*cm]
        rolls_table = Table(table_data, colWidths=col_widths)
        
        # Style du tableau sans bordures
        table_style = [
            # En-têtes avec dégradé
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0E4E95')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Corps du tableau
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fc')]),
            
            # Pas de bordures, padding minimal
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]
        
        rolls_table.setStyle(TableStyle(table_style))
        elements.append(rolls_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_averages_summary(self, rolls):
        """Construire le résumé des moyennes générales."""
        elements = []
        
        # Titre section
        subtitle = Paragraph("MOYENNES GÉNÉRALES", self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # Calculer les moyennes
        valid_rolls = [r for r in rolls if r.get('length') and float(r['length']) > 0]
        
        if not valid_rolls:
            no_data = Paragraph("Aucune donnée disponible pour le calcul des moyennes.", self.styles['InfoStyle'])
            elements.append(no_data)
            elements.append(Spacer(1, 20))
            return elements
        
        # Calculs des moyennes
        total_length = sum(float(r.get('length', 0)) for r in valid_rolls)
        avg_length = total_length / len(valid_rolls) if valid_rolls else 0
        
        # Moyennes épaisseurs
        left_thicknesses = [float(r.get('avg_thickness_left', 0)) for r in valid_rolls if r.get('avg_thickness_left')]
        right_thicknesses = [float(r.get('avg_thickness_right', 0)) for r in valid_rolls if r.get('avg_thickness_right')]
        
        avg_thickness_left = sum(left_thicknesses) / len(left_thicknesses) if left_thicknesses else 0
        avg_thickness_right = sum(right_thicknesses) / len(right_thicknesses) if right_thicknesses else 0
        
        # Moyenne grammage
        grammages = [float(r.get('grammage_calc', 0)) for r in valid_rolls if r.get('grammage_calc')]
        avg_grammage = sum(grammages) / len(grammages) if grammages else 0
        
        # Calculer MIN et MAX
        min_thickness_left = min(left_thicknesses) if left_thicknesses else 0
        max_thickness_left = max(left_thicknesses) if left_thicknesses else 0
        min_thickness_right = min(right_thicknesses) if right_thicknesses else 0
        max_thickness_right = max(right_thicknesses) if right_thicknesses else 0
        min_grammage = min(grammages) if grammages else 0
        max_grammage = max(grammages) if grammages else 0
        
        # Tableaux des moyennes avec MIN/MAX
        averages_data = [
            ['Paramètre', 'Minimum', 'Moyenne', 'Maximum', 'Échant.'],
            ['Longueur rouleaux', 
             f'{min(float(r.get("length", 0)) for r in valid_rolls):.2f} m' if valid_rolls else 'N/A',
             f'{avg_length:.2f} m', 
             f'{max(float(r.get("length", 0)) for r in valid_rolls):.2f} m' if valid_rolls else 'N/A',
             str(len(valid_rolls))],
            ['Épaisseur gauche', 
             f'{min_thickness_left:.3f} mm' if min_thickness_left > 0 else 'N/A',
             f'{avg_thickness_left:.3f} mm' if avg_thickness_left > 0 else 'N/A', 
             f'{max_thickness_left:.3f} mm' if max_thickness_left > 0 else 'N/A',
             str(len(left_thicknesses))],
            ['Épaisseur droite', 
             f'{min_thickness_right:.3f} mm' if min_thickness_right > 0 else 'N/A',
             f'{avg_thickness_right:.3f} mm' if avg_thickness_right > 0 else 'N/A', 
             f'{max_thickness_right:.3f} mm' if max_thickness_right > 0 else 'N/A',
             str(len(right_thicknesses))],
            ['Grammage calculé', 
             f'{min_grammage:.1f} g/m²' if min_grammage > 0 else 'N/A',
             f'{avg_grammage:.1f} g/m²' if avg_grammage > 0 else 'N/A', 
             f'{max_grammage:.1f} g/m²' if max_grammage > 0 else 'N/A',
             str(len(grammages))],
        ]
        
        avg_table = Table(averages_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 2*cm])
        avg_table.setStyle(TableStyle([
            # En-tête élégant
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EC1846')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            
            # Corps avec dégradé subtil
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fef5f7')]),
            
            # Pas de bordures, padding minimal
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Mise en évidence des colonnes MIN/MAX
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#d63384')),  # Minimum en rouge
            ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#198754')),  # Maximum en vert
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),  # Moyenne en gras
        ]))
        
        elements.append(avg_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_quality_details(self, rolls):
        """Construire les détails des contrôles qualité avec moyennes."""
        elements = []
        
        # Titre section
        subtitle = Paragraph("CONTRÔLES QUALITÉ", self.styles['CustomSubtitle'])
        elements.append(subtitle)
        
        # Vérifier s'il y a des contrôles qualité
        rolls_with_qc = [roll for roll in rolls if roll.get('quality_controls')]
        
        if not rolls_with_qc:
            no_controls = Paragraph("Aucun contrôle qualité disponible pour ces rouleaux.", self.styles['InfoStyle'])
            elements.append(no_controls)
            elements.append(Spacer(1, 20))
            return elements
        
        # Tableau détaillé des contrôles qualité par rouleau
        qc_headers = [
            'Roll ID', 'Micronaire G\n(mm)', 'Micronaire D\n(mm)', 
            'Extrait Sec\n(%)', 'LOI'
        ]
        
        qc_data = [qc_headers]
        
        # Collecte des données pour les moyennes
        micrometer_left_values = []
        micrometer_right_values = []
        dry_extract_values = []
        loi_count = 0
        
        for roll in rolls_with_qc:
            qc = roll.get('quality_controls')
            if qc:
                mic_left = qc.get('micrometer_left_avg')
                mic_right = qc.get('micrometer_right_avg')
                dry_ext = qc.get('dry_extract')
                
                # Collecter pour moyennes
                if mic_left:
                    micrometer_left_values.append(float(mic_left))
                if mic_right:
                    micrometer_right_values.append(float(mic_right))
                if dry_ext:
                    dry_extract_values.append(float(dry_ext))
                if qc.get('loi_given'):
                    loi_count += 1
                
                row = [
                    roll.get('roll_id', ''),
                    f"{mic_left:.3f}" if mic_left else '-',
                    f"{mic_right:.3f}" if mic_right else '-',
                    f"{dry_ext:.2f}" if dry_ext else '-',
                    'Oui' if qc.get('loi_given') else 'Non'
                ]
                qc_data.append(row)
        
        # Tableau détaillé
        if len(qc_data) > 1:
            qc_col_widths = [3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm]
            qc_table = Table(qc_data, colWidths=qc_col_widths)
            
            qc_table.setStyle(TableStyle([
                # En-têtes élégants
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0096D5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                
                # Corps avec alternance subtile
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
                
                # Pas de bordures, padding minimal
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            elements.append(qc_table)
            elements.append(Spacer(1, 15))
            
            # Moyennes des contrôles qualité
            avg_subtitle = Paragraph("MOYENNES DES CONTRÔLES QUALITÉ", 
                                   ParagraphStyle(
                                       name='QCAvgTitle',
                                       parent=self.styles['Normal'],
                                       fontSize=12,
                                       textColor=colors.HexColor('#0096D5'),
                                       spaceBefore=10,
                                       spaceAfter=10,
                                       alignment=TA_LEFT
                                   ))
            elements.append(avg_subtitle)
            
            # Calculer les moyennes, MIN et MAX
            avg_mic_left = sum(micrometer_left_values) / len(micrometer_left_values) if micrometer_left_values else 0
            avg_mic_right = sum(micrometer_right_values) / len(micrometer_right_values) if micrometer_right_values else 0
            avg_dry_extract = sum(dry_extract_values) / len(dry_extract_values) if dry_extract_values else 0
            loi_percentage = (loi_count / len(rolls_with_qc)) * 100 if rolls_with_qc else 0
            
            min_mic_left = min(micrometer_left_values) if micrometer_left_values else 0
            max_mic_left = max(micrometer_left_values) if micrometer_left_values else 0
            min_mic_right = min(micrometer_right_values) if micrometer_right_values else 0
            max_mic_right = max(micrometer_right_values) if micrometer_right_values else 0
            min_dry_extract = min(dry_extract_values) if dry_extract_values else 0
            max_dry_extract = max(dry_extract_values) if dry_extract_values else 0
            
            # Tableau des moyennes avec MIN/MAX
            avg_qc_data = [
                ['Paramètre', 'Minimum', 'Moyenne', 'Maximum', 'Échant.'],
                ['Micronaire Gauche', 
                 f'{min_mic_left:.3f} mm' if min_mic_left > 0 else 'N/A',
                 f'{avg_mic_left:.3f} mm' if avg_mic_left > 0 else 'N/A', 
                 f'{max_mic_left:.3f} mm' if max_mic_left > 0 else 'N/A',
                 str(len(micrometer_left_values))],
                ['Micronaire Droite', 
                 f'{min_mic_right:.3f} mm' if min_mic_right > 0 else 'N/A',
                 f'{avg_mic_right:.3f} mm' if avg_mic_right > 0 else 'N/A', 
                 f'{max_mic_right:.3f} mm' if max_mic_right > 0 else 'N/A',
                 str(len(micrometer_right_values))],
                ['Extrait Sec', 
                 f'{min_dry_extract:.2f} %' if min_dry_extract > 0 else 'N/A',
                 f'{avg_dry_extract:.2f} %' if avg_dry_extract > 0 else 'N/A', 
                 f'{max_dry_extract:.2f} %' if max_dry_extract > 0 else 'N/A',
                 str(len(dry_extract_values))],
                ['LOI Réalisée', '-', f'{loi_percentage:.1f} %', '-', f'{loi_count}/{len(rolls_with_qc)}'],
            ]
            
            avg_qc_table = Table(avg_qc_data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 2*cm])
            avg_qc_table.setStyle(TableStyle([
                # En-tête élégant
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#43B0B1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                
                # Corps avec dégradé subtil
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdfd')]),
                
                # Pas de bordures, padding minimal
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                
                # Mise en évidence des colonnes MIN/MAX
                ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#d63384')),  # Minimum en rouge
                ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#198754')),  # Maximum en vert
                ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),  # Moyenne en gras
            ]))
            
            elements.append(avg_qc_table)
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _build_footer(self):
        """Construire le pied de page élégant avec signature."""
        elements = []
        
        elements.append(Spacer(1, 40))
        
        # Ligne de séparation fine sans bordure
        from reportlab.graphics.shapes import Line
        line_drawing = Drawing(18*cm, 0.15*cm)
        line = Line(0, 0.075*cm, 18*cm, 0.075*cm)
        line.strokeColor = colors.HexColor('#EC1846')
        line.strokeWidth = 0.5
        line_drawing.add(line)
        elements.append(line_drawing)
        
        elements.append(Spacer(1, 20))
        
        # Zone de signature avec style amélioré
        signature_data = [
            ['Contrôlé par:', '________________________________', 
             'Date:', '____________________', 
             'Signature:', '________________________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*cm, 4*cm, 2*cm, 3*cm, 2.5*cm, 4*cm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#0E4E95')),  # Contrôlé par
            ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#0E4E95')),  # Date
            ('TEXTCOLOR', (4, 0), (4, 0), colors.HexColor('#0E4E95')),  # Signature
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(signature_table)
        
        # Note de bas de page avec style amélioré
        elements.append(Spacer(1, 30))
        date_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")
        footer_note = Paragraph(
            f"<i><font color='#43B0B1'>Document généré automatiquement le {date_generation}</font></i><br/>"
            "<font size=8><b>SGQ Ligne G - Saint-Gobain Quartz</b> - Système de Gestion de la Qualité</font>",
            ParagraphStyle(
                name='FooterNote',
                parent=self.styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#6c757d'),
                spaceBefore=10
            )
        )
        elements.append(footer_note)
        
        return elements
    
    def _create_gradient_bar(self):
        """Créer une barre élégante avec les couleurs du gradient Saint-Gobain."""
        # Couleurs du gradient Saint-Gobain
        colors_sg = [
            colors.HexColor('#43B0B1'),  # Turquoise
            colors.HexColor('#0096D5'),  # Bleu clair
            colors.HexColor('#0E4E95'),  # Bleu foncé
            colors.HexColor('#EC1846'),  # Rouge
            colors.HexColor('#F26F21'),  # Orange
        ]
        
        # Créer un drawing pour la barre fine sur toute la largeur
        drawing = Drawing(18*cm, 0.3*cm)
        
        # Largeur de chaque segment
        segment_width = 18*cm / len(colors_sg)
        
        # Dessiner chaque segment sans bordures
        for i, color in enumerate(colors_sg):
            x_pos = i * segment_width
            rect = Rect(x_pos, 0, segment_width, 0.3*cm)
            rect.fillColor = color
            rect.strokeColor = None  # Pas de bordure
            drawing.add(rect)
        
        return drawing
    
    def get_export_url(self, filename):
        """Retourner l'URL de téléchargement du fichier généré."""
        return f"/media/pick-lists/{filename}"