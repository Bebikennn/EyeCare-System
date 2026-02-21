import pickle

import pandas as pd


def main() -> None:
    model_data = pickle.load(open('models/eyecare_lightgbm_model.pkl', 'rb'))
    model = model_data['model']
    label_encoder = model_data['label_encoder']
    feature_names = model_data['feature_names']

    df = pd.read_csv('models/dataset/New_data.csv')
    row = df.iloc[[0]].copy()
    true_label = row['Diagnosis'].iloc[0] if 'Diagnosis' in row.columns else None

    X = row.drop(columns=['Diagnosis'])
    X = pd.get_dummies(X, columns=['Gender'], drop_first=True)

    for col in feature_names:
        if col not in X.columns:
            X[col] = 0
    X = X[feature_names]

    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    pred_label = label_encoder.inverse_transform([pred])[0]

    top3 = sorted(
        [(label_encoder.inverse_transform([i])[0], float(p)) for i, p in enumerate(proba)],
        key=lambda t: t[1],
        reverse=True,
    )[:3]

    print('true_label=', true_label)
    print('pred_label=', pred_label)
    print('top3=', top3)


if __name__ == '__main__':
    main()
