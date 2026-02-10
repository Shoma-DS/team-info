# Remotion ステップバイステップガイド

## ステップバイステップガイド

### ステップ1: 新しいRemotionプロジェクトの作成

Zsh環境のターミナルを開き、以下のコマンドを実行して新しいRemotionプロジェクトを作成します。

```bash
npm init video@latest
```

または

```bash
npx create-video@latest
```

コマンドを実行すると、テンプレートの選択を求められます。初心者の方には「Hello World」テンプレートがおすすめです。これにより、Remotionプロジェクトの基本的なファイルとフォルダ構造（例: `src/`ディレクトリ、`package.json`など）が自動的に設定されます。

### ステップ2: プロジェクト構造の理解

プロジェクトが作成されたら、主要なファイルとフォルダを確認しましょう。

*   `src/`: 動画のコンポーネントが格納されるディレクトリです。
    *   `src/Root.tsx`: Remotionアプリケーションのエントリーポイントであり、動画全体のコンポジション（構成）を定義します。Remotion Studioで表示される動画の「種類」や「設定」をここで管理します。
    *   `src/Composition.tsx` (または `src/HelloWorld.tsx`): 実際の動画コンテンツ（アニメーション、テキスト、画像など）を構築するReactコンポーネントです。このファイル内のコードが動画の具体的な「シーン」を形成します。
*   `package.json`: プロジェクトの依存関係と実行スクリプト（`npm start`など）が定義されています。

### ステップ3: Remotion Studioで動画をプレビューする

Zsh環境で、プロジェクトのルートディレクトリに移動し、以下のコマンドを実行してRemotion Studioを起動します。

```bash
npm start
```

または

```bash
npx remotion studio
```

このコマンドを実行すると、開発サーバーが起動し、ブラウザでRemotion Studioが開きます（通常は `http://localhost:3000`）。
Studioでは、`src/Root.tsx`で定義された各コンポジションのプレビューをリアルタイムで確認できます。コードを変更するたびに、ブラウザをリロードすることなく、即座に動画の動きやデザインの変化を確認できます。

### ステップ4: シンプルなアニメーションを作成する

`src/Composition.tsx` (または `src/HelloWorld.tsx`) ファイルを開いて編集し、簡単なテキストアニメーションを追加してみましょう。

```tsx
import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate, spring } from 'remotion';

export const MyComposition: React.FC = () => {
  const frame = useCurrentFrame(); // 現在のフレーム数を取得

  // テキストのフェードインアニメーション
  // [0, 30]はフレーム範囲、[0, 1]は透明度の範囲
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // テキストのY軸移動アニメーション (springアニメーション)
  // from: 初期Y座標, to: 最終Y座標。damping, stiffness, massでバネの挙動を調整
  const translateY = spring({
    frame,
    fps: 30, // プロジェクトのFPSに合わせる
    config: {
      damping: 200, // 減衰係数: 値を大きくすると振動が早く収まる
      stiffness: 100, // ばね定数: 値を大きくすると動きが速く硬くなる
      mass: 0.5, // 質量: 値を大きくすると動きが重くなる
    },
    from: -50, // 初期位置（上から-50px）
    to: 0, // 最終位置（0px）
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#1a1a1a', // 背景色
        justifyContent: 'center', // 中央揃え
        alignItems: 'center', // 中央揃え
      }}
    >
      <h1
        style={{
          fontFamily: 'sans-serif',
          fontSize: 100, // フォントサイズ
          color: 'white', // 文字色
          opacity, // 上記で定義した透明度アニメーションを適用
          transform: `translateY(${translateY}px)`, // 上記で定義したY軸移動アニメーションを適用
        }}
      >
        Remotionへようこそ！
      </h1>
    </AbsoluteFill>
  );
};
```

#### 変更による結果の確認
*   **`interpolate`の`[0, 30]`や`[0, 1]`の変更**:
    *   `[0, 30]`を`[0, 60]`に変更すると、テキストのフェードインが開始から60フレームかけてゆっくり行われるようになります。
    *   `[0, 1]`を`[0.5, 1]`に変更すると、フェードインが半透明の状態から始まるようになります。
    *   **結果**: Remotion Studioのプレビューで、テキストの表示開始タイミングやフェードインの速度、初期透明度が変化するのを確認できます。
*   **`spring`の`from`, `to`, `damping`, `stiffness`, `mass`の変更**:
    *   `from: -50`を`from: -200`に変更すると、テキストがより上の方から降りてくるようになります。
    *   `damping`を`10`に変更すると、バネの振動がより大きく、長く続くようになります。
    *   **結果**: Remotion Studioのプレビューで、テキストの移動開始位置、最終位置、そしてバネのようなアニメーションの動き方（弾み具合、速度）が変化するのを確認できます。
*   **`h1`タグ内の`style`プロパティの変更**:
    *   `fontSize: 100`を`fontSize: 150`に変更すると、テキストが大きくなります。
    *   `color: 'white'`を`color: 'lightblue'`に変更すると、文字色が水色に変わります。
    *   **結果**: Remotion Studioのプレビューで、テキストのサイズや色がリアルタイムで変化するのを確認できます。

#### `src/Root.tsx`での動画全体のプロパティ設定

`src/Root.tsx`ファイルを開いて、`Composition`コンポーネントのプロパティを確認・変更します。

```tsx
import { Composition } from 'remotion';
import { MyComposition } from './MyComposition'; // 作成したコンポーネントをインポート

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MyComposition" // 動画のID（複数のコンポジションを区別するために使用）
        component={MyComposition} // このIDでレンダリングするReactコンポーネントを指定
        durationInFrames={150} // 総フレーム数 (例: 5秒 * 30fps = 150フレーム)。動画の長さを決定
        fps={30} // フレームレート (Frames Per Second)。動画の滑らかさを決定
        width={1920} // 動画の幅 (ピクセル)
        height={1080} // 動画の高さ (ピクセル)
      />
    </>
  );
};
```

#### 変更による結果の確認
*   **`durationInFrames`の変更**:
    *   `durationInFrames={150}`を`durationInFrames={300}`に変更すると、動画全体の長さが2倍になります（30fpsの場合、5秒が10秒に）。
    *   **結果**: Remotion Studioのプレビューのタイムラインの総尺が変化し、動画が長くなるのを確認できます。
*   **`fps`の変更**:
    *   `fps={30}`を`fps={60}`に変更すると、動画がより滑らかになりますが、レンダリング時間は長くなります。
    *   **結果**: Remotion Studioのプレビューで、動画の滑らかさが変化するのを確認できます（ただし、プレビューのPCスペックに依存します）。
*   **`width`や`height`の変更**:
    *   `width={1920}, height={1080}`を`width={1280}, height={720}`に変更すると、動画の解像度がフルHDからHDに変わります。
    *   **結果**: Remotion Studioのプレビューのサイズが変化し、動画の出力解像度が変更されるのを確認できます。

変更を保存すると、Remotion Studioでリアルタイムにアニメーションが更新されるのが確認できます。

### ステップ5: 動画をレンダリングする

動画が完成したら、MP4ファイルとして出力（レンダリング）できます。Zsh環境で、プロジェクトのルートディレクトリに移動し、以下のコマンドを実行して動画をレンダリングします。

```bash
npx remotion render src/Root.tsx MyComposition out/video.mp4
```

*   `src/Root.tsx`: Remotionのメイン設定ファイルであり、動画のコンポジションが定義されているエントリーポイントです。
*   `MyComposition`: `src/Root.tsx`で`id`として定義したコンポジションの名前です。複数のコンポジションがある場合は、レンダリングしたいもののIDを指定します。
*   `out/video.mp4`: 出力される動画ファイルのパスと名前です。この例では、プロジェクトルートの`out`フォルダに`video.mp4`として保存されます。

レンダリングには時間がかかる場合があります。完了すると、指定したパスに動画ファイルが生成されます。

**よく使われるレンダリングオプション:**

*   `--codec`: 動画のコーデックを指定します（例: `h264`, `vp9`）。
*   `--crf`: 品質を設定します。小さいほど高品質ですが、ファイルサイズは大きくなります。デフォルトは`23`で、`0`（可逆圧縮）から`51`（最も低い品質）まで指定できます。
*   `--scale`: 出力解像度をスケーリングします（例: `--scale=0.5` で半分の解像度、`--scale=2` で2倍の解像度）。
*   `--frames`: 特定のフレーム範囲のみをレンダリングします（例: `--frames=0-90` で0フレーム目から90フレーム目までをレンダリング）。

## 次のステップ

*   **公式ドキュメント**: Remotionの公式ドキュメントは非常に充実しており、さらに高度な機能やAPIについて学ぶことができます。
*   **アニメーションの探求**: `Sequence`コンポーネントを使って複数のシーンを組み合わせたり、`spring`や`interpolate`以外の様々なアニメーション手法を試したりしてみましょう。
*   **データ駆動型動画**: JSONファイルなどのデータソースから動的にコンテンツを生成し、大量のパーソナライズされた動画を自動生成することもRemotionの強力な機能の一つです。

---

**重要: Remotion関連のスキルを使用する際は、常にこのガイドを事前に読み込み、プロジェクトの現在の状況と照らし合わせてください。**