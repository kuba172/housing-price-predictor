# analyze_data.py
import pandas as pd
import json
import os
from datetime import datetime
import numpy as np

def analyze_scraped_data(file_path):
    """Analizuje zebrane dane i pokazuje statystyki"""
    
    print(f"\n{'='*60}")
    print(f"ANALIZA DANYCH Z PLIKU: {os.path.basename(file_path)}")
    print(f"{'='*60}\n")
    
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        df = pd.read_csv(file_path)
    
    print(f"Podstawowe informacje:")
    print(f"   - Liczba ofert: {len(df)}")
    print(f"   - Liczba kolumn: {len(df.columns)}")
    print(f"   - Kolumny: {', '.join(df.columns)}\n")
    
    print(f"Kompletność danych:")
    for col in df.columns:
        if col not in ['url', 'scraped_at']:
            non_empty = df[col].notna().sum()
            if col == 'features':
                non_empty = sum(1 for f in df[col] if f and len(f) > 0)
            elif col == 'description':
                non_empty = sum(1 for d in df[col] if d and len(str(d).strip()) > 0)
            
            percentage = (non_empty / len(df)) * 100
            status = "OK" if percentage > 80 else "WARN" if percentage > 50 else "BRAK"
            print(f"   [{status}] {col}: {non_empty}/{len(df)} ({percentage:.1f}%)")
    
    if 'price' in df.columns and df['price'].notna().any():
        print(f"\nStatystyki cenowe:")
        prices = df['price'].dropna()
        print(f"   - Średnia cena: {prices.mean():,.0f} zł")
        print(f"   - Mediana ceny: {prices.median():,.0f} zł")
        print(f"   - Cena minimalna: {prices.min():,.0f} zł")
        print(f"   - Cena maksymalna: {prices.max():,.0f} zł")
        print(f"   - Odchylenie standardowe: {prices.std():,.0f} zł")
    
    if 'area' in df.columns and df['area'].notna().any():
        print(f"\nStatystyki powierzchni:")
        areas = df['area'].dropna()
        print(f"   - Średnia powierzchnia: {areas.mean():.1f} m²")
        print(f"   - Mediana powierzchni: {areas.median():.1f} m²")
        print(f"   - Min/Max: {areas.min():.1f} - {areas.max():.1f} m²")
        
        if 'price' in df.columns:
            df_with_both = df.dropna(subset=['price', 'area'])
            if len(df_with_both) > 0:
                df_with_both['price_per_m2'] = df_with_both['price'] / df_with_both['area']
                print(f"\nCena za m²:")
                print(f"   - Średnia: {df_with_both['price_per_m2'].mean():,.0f} zł/m²")
                print(f"   - Mediana: {df_with_both['price_per_m2'].median():,.0f} zł/m²")
    
    if 'rooms' in df.columns and df['rooms'].notna().any():
        print(f"\nRozkład liczby pokoi:")
        room_counts = df['rooms'].value_counts().sort_index()
        for rooms, count in room_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   - {int(rooms)} pokoje: {count} ofert ({percentage:.1f}%)")
    
    if 'floor' in df.columns and df['floor'].notna().any():
        print(f"\nRozkład pięter:")
        floor_counts = df['floor'].value_counts().head(10)
        for floor, count in floor_counts.items():
            print(f"   - {floor}: {count} ofert")
    
    if 'market' in df.columns and df['market'].notna().any():
        print(f"\nTyp rynku:")
        market_counts = df['market'].value_counts()
        for market, count in market_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   - {market}: {count} ofert ({percentage:.1f}%)")
    
    if 'address' in df.columns and df['address'].notna().any():
        print(f"\nNajpopularniejsze lokalizacje:")
        df['district'] = df['address'].apply(lambda x: str(x).split(',')[1].strip() if pd.notna(x) and ',' in str(x) else None)
        if df['district'].notna().any():
            district_counts = df['district'].value_counts().head(10)
            for district, count in district_counts.items():
                print(f"   - {district}: {count} ofert")
    
    print(f"\nPrzykładowe oferty z pełnymi danymi:")
    complete_data = df.dropna(subset=['price', 'area', 'rooms', 'address'])
    if len(complete_data) > 0:
        sample = complete_data.head(3)
        for idx, row in sample.iterrows():
            print(f"\n   Oferta {idx + 1}:")
            print(f"   - Tytuł: {row.get('title', 'Brak')[:60]}...")
            print(f"   - Cena: {row['price']:,.0f} zł")
            print(f"   - Powierzchnia: {row['area']} m²")
            print(f"   - Cena/m²: {row['price']/row['area']:,.0f} zł/m²")
            print(f"   - Pokoje: {int(row['rooms'])}")
            print(f"   - Lokalizacja: {row['address']}")
            if 'floor' in row and pd.notna(row['floor']):
                print(f"   - Piętro: {row['floor']}")
    else:
        print("   Brak ofert z kompletnymi danymi")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    data_dir = "data/raw"
    
    files = []
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith(('.json', '.csv')) and 'otodom' in file:
                file_path = os.path.join(data_dir, file)
                files.append((file_path, os.path.getmtime(file_path)))
    
    if files:
        files.sort(key=lambda x: x[1], reverse=True)
        latest_file = files[0][0]
        
        print(f"Analizuję najnowszy plik: {latest_file}")
        analyze_scraped_data(latest_file)
    else:
        print("Nie znaleziono plików z danymi w katalogu data/raw/")