# White Keeper

White Keeper は、日焼け量の積算値を簡単に見積もるための Streamlit アプリです。

## 機能
- 日付、外出時間、季節、天候、日焼け止めの有無を入力できます。
- 仕様に沿った係数を使って日焼け量を算出します。
- 計算結果をローカルの JSON へ保存し、履歴として一覧表示できます。

## 実行方法
```bash
streamlit run src/white_keeper/app.py
```

## テスト
```bash
pytest -q
```
