# 引継ぎ資料: 回路図ワイヤー整理 (Codex向け)

作成日: 2026-09-14 / 作成者: Claude (Sonnet 5)

## 依頼内容(スコープ)

対象は **`AK4490DAC.kicad_sch`(回路図)のワイヤーの見た目の整理のみ**。

- 電気的なネット接続(どのピンとどのピンが繋がっているか)は**変更しない**
- ワイヤーの経路・ジャンクション位置・ラベルの配置など、**見た目(交差・重なり・遠回り)をきれいにする**のが目的
- 部品の定数値・フットプリント・ピン配置の修正は対象外
- `AK4490DAC.kicad_pcb`(基板)は対象外 ※後述の通りまだトレース配線が0本の状態で、今回は触らない

## プロジェクト概要

AKM AK4490(32bit DACチップ)を使ったUSB DACのKiCadプロジェクト。

**注意: `README.md` の内容は古いまま**(PCM2704C + AK4118 + SPDIF光入力 + SA9227構想の説明)。
直近の一連のコミットで USB入力段を XMOS XU316 ベースに全面移行しているため、実態と乖離している。README は今回のタスクでは信用しないこと。

### 現在の回路構成(2026-09-13時点、最新コミット)

```
PC --USB-C(J2)--> ISOUSB211DPR(U3, USBアイソレータ) --USB2.0--> XU316(U2, XMOS xcore.ai)
                                                                        | I2S (BICK/LRCK/SDATA/MCLK)
                                                                        v
                                                                   AK4490(U6, DAC)
                                                                        | 差動アナログ出力
                                                                        v
                                                              MUSES8920/TL072 出力段(IC5, IC8-9)
                                                                        |
                                                                        v
                                                                    ライン出力
```

- **U2 = XU316-1024-QF60B-C24**: 自作60ピンシンボル + 自作パラメトリックQFN-60(0.4mmピッチ)フットプリント。**フットプリント寸法は推定値**(QF60Bというパッケージ呼称からの逆算)。実物の機械図面が手に入り次第、ピン1コーナーの向き含めて検証が必要(基板発注前必須)
- **U3 = ISOUSB211DPR**: USBアイソレータ。J2(USB_GNDドメイン)とXU316(メインGND)を絶縁。Side1はJ2のVBUSからバスパワー(内部LDOでV3P3V1/V1P8V1生成)、Side2は外部供給の+3V3_XU/+1V8_XUレール
- **U4 = W25Q32JVSSIQ**: QSPIブートフラッシュ。ファームウェア(未着手・スコープ外)用
- **Y1**: 24MHz水晶(XU316用)。負荷容量値は暫定(18pF、他クリスタルに合わせただけ)
- **IC10 (LP5907 1.8V) / IC11 (TPS7A20 ADJ品 + R29/R30で0.9V)**: XU316の電源用に新設。IC1はAK4118撤去に伴い+3V3_XUに転用
- **I2Sの信号名(_BICK/_LRCK/_SDATA/_MCLK)はXU316のGPIO割り当てのプレースホルダ**。実際のピン機能はファームウェアで決まるため、この命名はあくまで仮
- JP2: 5ピンJTAGデバッグヘッダ

### 撤去済み(過去にあったが現在は存在しない部品)

PCM2704C、AK4118、SPDIF光入力(TORX147FT)、DA103C絶縁トランス、SA9227、74LS157マルチプレクサ、24LC02 EEPROM ― これらは全て撤去済み。回路図中に見当たらなくても正常。

## ファイル構成の注意点

- `AK4490DAC.kicad_sch` — 触ってよい対象(今回のメイン)
- `AK4490DAC.kicad_sym` — このプロジェクト専用ライブラリ(XU316, ISOUSB211等のカスタムシンボル定義)。ワイヤー整理では触らない想定
- `AK4490DAC.kicad_pcb` — **触らない**。フットプリント14個が配置されているだけで、配線トレース・ビア・ベタ(zone)は0。今回のスコープ外
- `hardware/generate_schematic.py` と `.codex-work/` ディレクトリ — **これは別セッションで走らせた、ゼロから回路図を自動生成する未完成の試作コード**。現行の `AK4490DAC.kicad_sch` とは無関係で、書き込み先も別パス(`hardware/*.kicad_sch`)。混同しないこと。触る必要なし
- `AK4490DAC-backups/` — 過去のZIPバックアップ。参照不要
- `reference/` — 旧Eagle設計の部品表・実装データ(参考用、現行設計とは対応が薄い)

## 既知の状態・現在のERC結果

`kicad-cli sch erc` を実行すると **135件の違反**が出るが、これは**全て既知・想定内**のもの:

| type | 件数 | 内容・原因 |
|---|---:|---|
| pin_not_connected | 89 | 主に電源系IN/EN配線がまだ「ユーザーの本配線パス待ち」の状態(意図的に未接続のまま残されている) |
| power_pin_not_driven | 30 | 同上、電源ネットの供給元配線待ち |
| pin_not_driven | 8 | 主にU1(74LS06N)まわり、未使用ゲート等 |
| lib_symbol_mismatch | 5 | 標準ライブラリ(TL072, 74LS06N, USB_C_Receptacle等)のキャッシュと現在のライブラリ版の差分。実害なし、警告のみ |
| missing_unit | 1 | U1(74LS06N)の一部ユニット未配置 |
| missing_power_pin | 1 | 既知の1件 |
| missing_input_pin | 1 | U1(74LS06N)関連 |

**作業完了の目安**: ワイヤー整理後にもう一度 `sch erc` を実行し、この件数・カテゴリの内訳が(ネット接続を変えていなければ)同じままであることを確認する。件数が増えていたら、意図せずネットを切ってしまった可能性が高い。

コマンド例:
```
"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" sch erc --format json --output erc_after.json AK4490DAC.kicad_sch
```

## 過去にハマった落とし穴(要注意)

1. **一括での大量ワイヤー挿入でkicad-cliがsegfaultした事例あり**(2026-09-13、XU316追加時)。原因は特定できず(個別に分割して再現させると問題なし)。大きな変更は一度に流し込まず、**小分けにして都度 `sch erc` で読み込み確認**しながら進めるのが安全
2. **座標の偶然の一致(coordinate collision)によるバグ**が過去に発生している。ワイヤーやジャンクションの座標を機械的にずらす/移動する際は、既存の他要素と座標が衝突しないよう注意
3. 部品削除時、ダングリングになった配線・ラベルはUUID一致で特定して削除する手法が過去使われている(座標ベースでの削除は事故のもと)

## 推奨の進め方

1. 現状の `sch erc` 結果(件数・カテゴリ)をまず記録しておく(このドキュメントの表と照合)
2. ワイヤー整理は**電気的に等価な経路の付け替え**(交差の解消、直角配線への整列、ラベル位置調整など)にとどめる
3. まとまった単位(シート単位・回路ブロック単位など)で区切り、都度 `git commit` して差分を追えるようにする
4. 各区切りごとに `sch erc` を実行し、違反の件数・カテゴリが変化していないことを確認する
5. 完了後、最終的な `sch erc` 結果をコミットメッセージに残す(このプロジェクトの既存コミットの慣習に合わせる)

## 参考: 直近のコミット履歴

```
8e62d29 Add XU316, ISOUSB211, QSPI flash: USB/SPDIF -> XMOS migration
ce33006 Remove PCM2704C, AK4118 and SPDIF path ahead of XU316 migration
9f22a35 Convert power/ground net labels to real KiCad power symbols
2c88caa Decide SPDIF input as optical-only, switch USB to Type-C
5c2dc8f Consolidate output op-amps: move R channel onto IC5, remove IC6
```

KiCadバージョン: 10.0(`C:\Program Files\KiCad\10.0`)
